"""PostgreSQL adapter for the AnySet repository."""

from datetime import datetime
import logging
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool

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

from .settings import PostgresSettings, postgres_settings

logger = logging.getLogger(__name__)


class PostgresAdapter(IRepository, metaclass=SingletonMeta):
    """PostgreSQL implementation of IRepository."""

    _pool: Any = None

    def __init__(self, dataset: Dataset):
        """Initialize the PostgreSQL repository.

        Args:
            dataset: Dataset - The dataset definition object
        """
        super().__init__(dataset)

        settings = {**postgres_settings.model_dump(), **dataset.adapter_config}
        self._setup_connection_pool(PostgresSettings(**settings))
        self.dataset = dataset

    def _setup_connection_pool(self, settings: PostgresSettings) -> None:
        """Set up the connection pool for PostgreSQL."""
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=settings.pool_min_size,
                maxconn=settings.pool_max_size,
                host=settings.host,
                port=settings.port,
                user=settings.user,
                password=settings.password,
                database=settings.database,
            )
            logger.info(
                "PostgreSQL connection pool established to %s:%s/%s",
                settings.host,
                settings.port,
                settings.database,
            )
        except psycopg2.Error as ex:
            raise RuntimeError(f"FailedConnectPostgreSQLConnectionPool {ex}") from ex

    async def execute_query(self, query: QueryRequest) -> ResultSet:
        """Execute a query on a PostgreSQL database.

        Args:
            query: The query request

        Returns:
            The query response
        """
        if self._pool is None:
            raise RuntimeError("PostgreSQLConnectionPoolNotInitialized")

        conn = None
        try:
            conn = self._pool.getconn()

            sql, params = self._build_sql_query(query)
            logger.info(sql)
            logger.info(params)

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                columns = [
                    BaseResultSetColumn(
                        alias=desc[0],
                        breakdown=None,
                        data=[r[desc[0]] for r in rows],
                    )
                    for desc in cursor.description
                ]

                return ResultSet(
                    dataset=query.dataset._id,
                    version=query.dataset.version,
                    rows=len(rows),
                    columns=columns,
                )

        except psycopg2.Error as e:
            logger.error("Error executing PostgreSQL query: %s", e)
            if conn is not None:
                conn.rollback()
            raise RuntimeError(f"Database query error: {e}") from e

        finally:
            if conn is not None and self._pool is not None:
                self._pool.putconn(conn)

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
        """Process filter options from a database row.

        Args:
            row: Database row containing filter options

        Returns:
            Processed filter option values

        Raises:
            ValueError: If column type is not supported
        """
        col_type = row["k"]
        if col_type == ColumnType.text_category.value:
            return row["v"]
        elif col_type == ColumnType.boolean.value:
            return [str(v).lower() == "true" for v in row["v"]]
        elif col_type == ColumnType.datetime.value:
            return [datetime.fromisoformat(str(v)) for v in row["v"]]
        elif col_type == ColumnType.numeric_fact.value:
            return [float(v) for v in row["v"]]
        else:
            raise ValueError(f"InvalidColumnType {col_type}")

    def _create_simple_filter_options_statement(
        self,
        table: str,
        column_name: str,
    ) -> str:
        """Create a SQL statement for retrieving filter options values from a column.

        Args:
            table: The table name
            column_name: The column name

        Returns:
            SQL statement

        Raises:
            ValueError: If column type is not supported
        """
        col_type = self.dataset.dataset_tables[table].columns[column_name].column_type.value

        if col_type in [ColumnType.boolean.value, ColumnType.text_category.value]:
            arr = f"ARRAY_AGG(DISTINCT {column_name}::varchar)"
        elif col_type in [ColumnType.numeric_fact.value, ColumnType.datetime.value]:
            arr = f"ARRAY[MIN({column_name}::varchar), MAX({column_name}::varchar)]"
        else:
            raise ValueError(f"InvalidColumnType {col_type}")

        return f"""
        SELECT
            '{column_name}' AS n,
            '{col_type}' AS k,
            {arr} AS v
        FROM "{table}"
        """

    async def _get_simple_filter_options(
        self,
        fields: list[tuple[str, str]],
    ) -> FilterOptions:
        """Get filter options for non-hierarchical fields.

        Args:
            fields: List of (table_name, column_name) tuples

        Returns:
            Filter options
        """
        if not fields:
            return []

        statements = [
            self._create_simple_filter_options_statement(
                table=table,
                column_name=column_name,
            )
            for table, column_name in fields
        ]

        try:
            conn = self._pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(" UNION ALL ".join(statements))
                rows = cursor.fetchall()

        except psycopg2.Error as e:
            logger.error("Error executing PostgreSQL query: %s", e)
            raise RuntimeError(f"Database query error: {e}") from e
        finally:
            if conn is not None and self._pool is not None:
                self._pool.putconn(conn)

        return [
            CategoricalFilterOption(
                name=row["n"],
                kind="CategoricalFilterOption",
                values=self._process_filter_options(row),
            )
            if row["k"]
            in [
                ColumnType.text_category.value,
                ColumnType.boolean.value,
            ]
            else MinMaxFilterOption(
                name=row["n"],
                kind="MinMaxFilterOption",
                values=tuple(self._process_filter_options(row)),
            )
            for row in rows
        ]

    def _walk_hierarchy(
        self,
        data: pd.DataFrame,
        columns: list[str],
        index: int = 0,
    ) -> CategoricalFilterOption:
        """Walk the hierarchy and return a CategoricalFilterOption with nested children.

        Args:
            data: The data to walk the hierarchy on
            columns: The columns to walk the hierarchy on
            index: The index of the column to walk the hierarchy on

        Returns:
            CategoricalFilterOption with nested children
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
        """Get filter options for a single hierarchy.

        Args:
            key: The hierarchy key
            fields: List of (table, column, table.column) tuples

        Returns:
            CategoricalFilterOption for the hierarchy
        """
        # TODO: Add support for multi-table datasets
        table = f'"{fields[0][0]}"'

        selected_cols = ", ".join([f'{f[0]}.{f[1]} AS "{f[2]}"' for f in fields])
        group_by = ", ".join([f'"{f[2]}"' for f in fields])
        order_by = ", ".join([f'"{f[2]}"' for f in fields])
        statement = f"""
        SELECT DISTINCT {selected_cols}
        FROM {table}
        GROUP BY {group_by}
        ORDER BY {order_by}
        """

        try:
            conn = self._pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(statement)
                data = pd.DataFrame(cursor.fetchall())
        except psycopg2.Error as e:
            logger.error("Error executing PostgreSQL query: %s", e)
            raise RuntimeError(f"Database query error: {e}") from e
        finally:
            if conn is not None and self._pool is not None:
                self._pool.putconn(conn)

        return self._walk_hierarchy(data=data, columns=[v[2] for v in fields])

    async def _get_filter_options_in_category_hierarchies(self) -> FilterOptions:
        """Get filter options for fields in category hierarchies.

        Returns:
            Filter options for hierarchical fields
        """
        return [
            await self._get_filter_options_for_single_hierarchy_definition(
                key,
                [(f[0], f[1], f"{f[0]}.{f[1]}") for f in fields],
            )
            for key, fields in self.dataset.category_hierarchies.items()
        ]

    def _build_sql_query(self, query: QueryRequest) -> tuple[str, dict[str, Any]]:
        """Build a SQL query from a QueryRequest.

        Args:
            query: The query request

        Returns:
            Tuple of SQL string and parameters
        """
        source = f'"{query.table_name}"'
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

        for qorder in query.order_by:
            order_by.append(f'"{qorder.column_name}" {qorder.direction}')

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
