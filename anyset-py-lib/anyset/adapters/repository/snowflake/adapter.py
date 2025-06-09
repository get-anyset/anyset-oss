"""Snowflake implementation of IRepository."""

from datetime import datetime
import logging
from typing import Any

from orjson import loads as orjson_loads  # pylint: disable=E0611
import pandas as pd
import snowflake.connector
from sqlalchemy.dialects import registry
import sqlalchemy.pool as pool

from anyset.core.models import (
    BaseResultSetColumn,
    CategoricalFilterOption,
    ColumnType,
    Dataset,
    FilterOptions,
    MinMaxFilterOption,
    QueryRequest,
    QueryRequestAggregation,
    QueryRequestCustomAggregation,
    ResultSet,
)
from anyset.core.repository_interface import IRepository
from anyset.core.singleton_meta import SingletonMeta

from .settings import SnowflakeSettings, snowflake_settings

logger = logging.getLogger(__name__)


class SnowflakeAdapter(IRepository, metaclass=SingletonMeta):
    """Snowflake implementation of IRepository."""

    _pool: pool.QueuePool

    def __init__(self, dataset: Dataset):
        """Initialize the PostgreSQL repository.

        Args:
            dataset: Dataset - The dataset definition object
        """
        registry.register("snowflake", "snowflake.sqlalchemy", "dialect")

        super().__init__(dataset)

        self.settings = SnowflakeSettings(
            **{
                **snowflake_settings.model_dump(),
                **dataset.adapter_config,
            }
        )
        self._setup_connection_pool()

    def _get_connection(self) -> snowflake.connector.SnowflakeConnection:
        """Get a Snowflake connection."""
        settings = self.settings.model_dump(
            exclude_none=True,
            exclude={"private_key_str", "private_key_passphrase"},
            by_alias=True,
        )
        return snowflake.connector.connect(**settings)

    def _setup_connection_pool(self) -> None:
        """Set up the connection pool for PostgreSQL."""
        try:
            self._pool = pool.QueuePool(
                self._get_connection,  # type: ignore
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.pool_max_overflow,
            )
            logger.info(
                "Snowflake connection pool established to %s:%s/%s",
                self.settings.account,
                self.settings.schema_,
                self.settings.database,
            )
        except snowflake.connector.errors.Error as ex:
            raise RuntimeError(f"SnowflakeConnectionError {ex}") from ex

    async def execute_query(self, query: QueryRequest) -> ResultSet:
        """Execute a query on the database.

        Args:
            query: QueryRequest - The query to execute

        Returns:
            ResultSet - The result set from the query
        """
        if self._pool is None:
            raise RuntimeError("PostgreSQLConnectionPoolNotInitialized")

        sql, params = self._build_sql_query(query)

        try:
            conn = self._pool.connect()
            cursor = conn.cursor()

            cursor.execute(sql, params)
            data = cursor.fetchall()
            columns = [
                BaseResultSetColumn(
                    alias=col[0],
                    breakdown=None,
                    data=[row[i] for row in data],
                )
                for i, col in enumerate(cursor.description)
            ]
            results = ResultSet(
                dataset=self.dataset.name,
                version=self.dataset.version,
                rows=cursor.rowcount or 0,
                columns=columns,
            )
        except snowflake.connector.errors.Error as ex:
            raise RuntimeError(f"SnowflakeConnectionError {ex}") from ex
        finally:
            cursor.close() if cursor else None
            conn.close() if conn else None

        return results

    def _build_sql_query(self, query: QueryRequest) -> tuple[str, dict[str, Any]]:
        """Build a SQL query from a QueryRequest.

        Args:
            query: The query request

        Returns:
            Tuple of SQL string and parameters
        """
        source = f"{self.settings.database}.{self.settings.schema_}.{query.table_name}"
        select: list[str] = []
        where: list[str] = []
        order_by: list[str] = []

        params: dict[str, Any] = {}
        param_idx = 0

        for qselect in query.select:
            select.append(f'"{qselect.column_name}" AS "{qselect.alias or qselect.column_name}"')

            # Add to group by if needed
            # if query.breakdown is not None:
            #     group_by_parts.append(f'"{column_name}"')

        for qagg in query.aggregations:
            if isinstance(qagg, QueryRequestAggregation):
                select.append(
                    f'{qagg.aggregation_function}("{qagg.column_name}") AS "{qagg.alias}"'
                )
            elif isinstance(qagg, QueryRequestCustomAggregation):
                select.append(f'{qagg.aggregation_function} AS "{qagg.alias}"')

        for qfilter in query.filters:
            if qfilter.kind == "QueryRequestFilterCategory" and qfilter.values:
                param_name = f"p{param_idx}"
                where.append(f'"{qfilter.column_name}" IN (%({param_name})s)')
                params[param_name] = f"{','.join(qfilter.values)}"
                param_idx += 1
            elif qfilter.kind == "QueryRequestFilterFact" and qfilter.values:
                min_val, max_val = qfilter.values

                if min_val is not None:
                    param_name = f"p{param_idx}"
                    where.append(f'"{qfilter.column_name}" >= %({param_name})s')
                    params[param_name] = min_val
                    param_idx += 1

                if max_val is not None:
                    param_name = f"p{param_idx}"
                    where.append(f'"{qfilter.column_name}" <= %({param_name})s')
                    params[param_name] = max_val  # This is a single value, not a list
                    param_idx += 1

        order_by.extend(
            [f'"{qorder.column_name}" {qorder.direction}' for qorder in query.order_by]
            if query.order_by
            else ["1 ASC"]
        )

        offset = query.pagination.offset
        limit = query.pagination.limit

        sql = f"SELECT {', '.join(select) or '*'} FROM {source}"

        if where:
            sql += f" WHERE {' AND '.join(where)}"
        if query.group_by:
            sql += f" GROUP BY {', '.join(query.group_by)}"
        if order_by:
            sql += f" ORDER BY {', '.join(order_by)}"
        if limit is not None:
            sql += f" LIMIT {limit}"
        if offset is not None:
            sql += f" OFFSET {offset}"

        return sql, params

    async def get_filter_options(self) -> FilterOptions:
        """Get filter options from the database.

        Returns:
            Filter options for the UI
        """
        if self._pool is None:
            raise RuntimeError("PostgreSQLConnectionPoolNotInitialized")

        non_hierarchical_fields = []
        for table_name, column_names in [
            *self.dataset.dataset_cols_text_category.items(),
            *self.dataset.dataset_cols_boolean.items(),
            *self.dataset.dataset_cols_numeric_fact.items(),
            *self.dataset.dataset_cols_datetime.items(),
        ]:
            for column_name in column_names:
                if not self.dataset.is_col_in_category_hierarchy(table_name, column_name):
                    non_hierarchical_fields.append((table_name, column_name))

        return (
            await self._get_filter_options_in_category_hierarchies()
            + await self._get_simple_filter_options(non_hierarchical_fields)
        )

    def _process_filter_options(self, row: dict[str, Any]) -> list[Any]:
        col_type = row["K"]
        if col_type in [ColumnType.text_category]:
            return orjson_loads(row["V"])
        elif col_type in [ColumnType.boolean]:
            return [i == "true" for i in orjson_loads(row["V"])]
        elif col_type in [ColumnType.datetime]:
            return [datetime.fromisoformat(i) for i in orjson_loads(row["V"])]
        elif col_type in [ColumnType.numeric_fact]:
            return [float(i) for i in orjson_loads(row["V"])]
        else:
            raise ValueError(f"InvalidColumnType {col_type}")

    def _create_simple_filter_options_statement(
        self,
        table: str,
        column_name: str,
    ) -> str:
        """Create a SQL statement for retrieving filter options values from a column.

        Args:
            table: str - The table name
            column_name: str - The column name

        Returns:
            str - The SQL statement
        """
        col_type = self.dataset.dataset_tables[table].columns[column_name].column_type.value

        if col_type in [ColumnType.boolean, ColumnType.text_category]:
            arr = f"ARRAY_AGG(DISTINCT {column_name}::varchar)"
        elif col_type in [ColumnType.numeric_fact, ColumnType.datetime]:
            arr = f"ARRAY_CONSTRUCT(MIN({column_name}), MAX({column_name}))"
        else:
            raise ValueError(f"InvalidColumnType {col_type}")

        return f"""
        SELECT
            '{column_name}' AS n,
            '{col_type}' AS k,
            {arr} AS v
        FROM {self.settings.database}.{self.settings.schema_}.{table}
        """

    async def _get_simple_filter_options(
        self,
        fields: list[tuple[str, str]],
    ) -> FilterOptions:
        """Get filter options from the database.

        Returns:
            Filter options for the UI
        """
        """
        split hierarchical and non-hierarchical columns
        run each set through their respective get_filter_options methods
        combine results into a single FilterOptions object
        """
        if self._pool is None:
            raise RuntimeError("PostgreSQLConnectionPoolNotInitialized")

        statements = [
            self._create_simple_filter_options_statement(
                table=table,
                column_name=column_name,
            )
            for table, column_name in fields
        ]

        try:
            conn = self._pool.connect()
            cursor = conn.cursor()
            cursor.execute(" UNION ALL ".join(statements))
            data = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])

            data["V"] = data.apply(
                lambda row: self._process_filter_options(row),
                axis=1,
            )
        except snowflake.connector.errors.Error as ex:
            raise RuntimeError(f"SnowflakeConnectionError {ex}") from ex
        finally:
            cursor.close() if cursor else None
            conn.close() if conn else None

        return [
            CategoricalFilterOption(
                name=row["N"],
                kind="CategoricalFilterOption",
                values=row["V"],
            )
            if row["K"]
            in [
                ColumnType.text_category.value,
                ColumnType.boolean.value,
            ]
            else MinMaxFilterOption(
                name=row["N"],
                kind="MinMaxFilterOption",
                values=(row["V"][0], row["V"][1]),
            )
            for _, row in data.iterrows()
        ]

    def _walk_hierarchy(
        self,
        data: pd.DataFrame,
        columns: list[str],
        index: int = 0,
    ) -> CategoricalFilterOption:
        """Walk the hierarchy and return a CategoricalFilterOption with nested children.

        Args:
            data: pd.DataFrame - The data to walk the hierarchy on
            columns: list[str] - The columns to walk the hierarchy on
            index: int - The index of the column to walk the hierarchy on

        Returns:
            CategoricalFilterOption - The CategoricalFilterOption with nested children
        """
        col = columns[index]
        unique_values: list[str] = pd.Series(data[col].dropna().unique()).tolist()

        values: list[str] | list[tuple[str, CategoricalFilterOption]]
        if (index + 1) == len(columns):
            values = unique_values
        else:
            values = [
                (v, self._walk_hierarchy(data[data[col] == v], columns, index + 1))
                for v in unique_values
            ]

        return CategoricalFilterOption(
            name=columns[index],
            values=values,
        )

    async def _get_filter_options_for_single_hierarchy_definition(
        self,
        key: str,
        fields: list[tuple[str, str, str]],
    ) -> CategoricalFilterOption:
        """Get filter options for a single hierarchy from the database.

        Args:
            key: str - The key of the hierarchy
            fields: list[tuple[str, str]] - The fields of the hierarchy [table, column, table.column]

        Returns:
            Filter options for the UI
        """
        # TODO: Add support for multi-table datasets
        table = f"{self.settings.database}.{self.settings.schema_}.{fields[0][0]}"

        selected_cols = ", ".join([f'{f[0]}.{f[1]} AS "{f[2]}"' for f in fields])
        group_by = ", ".join([f'"{f[2]}"' for f in fields])
        order_by = ", ".join([f'"{f[2]}"' for f in fields])
        statement = f"""
        SELECT
            DISTINCT {selected_cols}
        FROM {table}
        GROUP BY {group_by}
        ORDER BY {order_by}
        """

        try:
            conn = self._pool.connect()
            cursor = conn.cursor()
            cursor.execute(statement)
            data = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
        except snowflake.connector.errors.Error as ex:
            raise RuntimeError(f"SnowflakeConnectionError {ex}") from ex
        finally:
            cursor.close() if cursor else None
            conn.close() if conn else None

        return self._walk_hierarchy(data=data, columns=[v[2] for v in fields])

    async def _get_filter_options_in_category_hierarchies(self) -> FilterOptions:
        """Get filter options for fields in a category hierarchy from the database.

        TODO: Add support for multi-table datasets.

        Returns:
            Filter options for the UI
        """
        return [
            await self._get_filter_options_for_single_hierarchy_definition(
                key,
                [(f[0], f[1], f"{f[0]}.{f[1]}") for f in fields],
            )
            for key, fields in self.dataset.category_hierarchies.items()
        ]
