"""Snowflake implementation of IRepository."""

from datetime import datetime
import logging
from typing import Any

from orjson import loads as orjson_loads
import pandas as pd
import snowflake.connector
from sqlalchemy.dialects import registry
import sqlalchemy.pool as pool

from ..models import (
    CategoricalFilterOption,
    ColumnType,
    Dataset,
    FilterOptions,
    MinMaxFilterOption,
    QueryRequest,
    Resultset,
)
from ..repository_interface import IRepository
from ..singleton_meta import SingletonMeta
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
        return snowflake.connector.connect(**self.settings.model_dump())

    def _setup_connection_pool(self) -> None:
        """Set up the connection pool for PostgreSQL."""
        try:
            self._pool = pool.QueuePool(
                self._get_connection,
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

    async def execute_query(self, query: QueryRequest) -> Resultset:
        """Execute a query on the database.

        Args:
            query: QueryRequest - The query to execute

        Returns:
            Resultset - The resultset from the query
        """
        return Resultset(
            dataset=self.dataset._id,
            version=self.dataset.version,
            rows=0,
            columns=[],
        )

    def _create_filter_options_statement(self, table: str, columns: list[str]) -> list[str]:
        """Create a SQL statement for retrieving filter options values from a column.

        Args:
            table: str - The table name
            columns: list[str] - The column names

        Returns:
            str - The SQL statement
        """
        statements = []
        for col in columns:
            col_type = self.dataset.dataset_tables[table].columns[col].column_type.value

            if col_type in [ColumnType.boolean, ColumnType.text_category]:
                arr = f"ARRAY_AGG(DISTINCT {col}::varchar)"
            elif col_type in [ColumnType.numeric_fact, ColumnType.datetime]:
                arr = f"ARRAY_CONSTRUCT(MIN({col}), MAX({col}))"
            else:
                raise ValueError(f"InvalidColumnType {col_type}")

            statements.append(f"""
            SELECT
                '{col}' AS n,
                '{col_type}' AS k,
                {arr} AS v
            FROM {self.settings.database}.{self.settings.schema_}.{table}
            """)
        return statements

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

    async def get_filter_options(self) -> FilterOptions:
        """Get filter options from the database.

        Returns:
            Filter options for the UI
        """
        if self._pool is None:
            raise RuntimeError("PostgreSQLConnectionPoolNotInitialized")

        statements = []
        for k, v in [
            *self.dataset.dataset_cols_text_category.items(),
            *self.dataset.dataset_cols_boolean.items(),
            *self.dataset.dataset_cols_numeric_fact.items(),
            *self.dataset.dataset_cols_datetime.items(),
        ]:
            statements.extend(self._create_filter_options_statement(k, v))

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
