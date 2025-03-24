"""PostgreSQL adapter for the AnySet repository."""

import logging
from typing import Any

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

from ..models import (
    BaseResultsetColumn,
    FilterOptionCategory,
    FilterOptionMinMax,
    QueryRequestAggregation,
    QueryRequestCustomAggregation,
    QueryRequestSelect,
)
from ..repository import FilterOptions, QueryRequest, RepositoryPort, Resultset
from .settings import PostgresSettings, postgres_settings

logger = logging.getLogger(__name__)


class PostgresRepository(RepositoryPort):
    """PostgreSQL implementation of RepositoryPort."""

    def __init__(self, settings: PostgresSettings = postgres_settings):
        """Initialize the PostgreSQL repository.

        Args:
            settings: PostgreSQL connection settings
        """
        self.settings = settings
        self._pool: Any = None
        self._setup_connection_pool()

    def _setup_connection_pool(self) -> None:
        """Set up the connection pool for PostgreSQL."""
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=self.settings.pool_min_size,
                maxconn=self.settings.pool_max_size,
                host=self.settings.host,
                port=self.settings.port,
                user=self.settings.user,
                password=self.settings.password,
                database=self.settings.database,
            )
            logger.info(
                "PostgreSQL connection pool established to %s:%s/%s",
                self.settings.host,
                self.settings.port,
                self.settings.database,
            )
        except psycopg2.Error as ex:
            raise RuntimeError(f"FailedConnectPostgreSQLConnectionPool {ex}") from ex

    async def execute_query(self, query: QueryRequest) -> Resultset:
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
            print(query.group_by)
            print(sql)
            print(params)

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                columns = [
                    BaseResultsetColumn(
                        alias=desc[0],
                        breakdown=None,
                        data=[r[desc[0]] for r in rows],
                    )
                    for desc in cursor.description
                ]

                return Resultset(
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

        conn = None
        filter_options: list[FilterOptionCategory | FilterOptionMinMax] = []

        try:
            conn = self._pool.getconn()

            with conn.cursor() as cursor:
                # Get category columns filter options
                category_options = self._get_category_filter_options(cursor)
                filter_options.extend(category_options)

                # Get numeric (fact) columns filter options
                numeric_options = self._get_numeric_filter_options(cursor)
                filter_options.extend(numeric_options)

            return filter_options

        except psycopg2.Error as e:
            logger.error("Error getting filter options: %s", e)
            raise RuntimeError(f"Database error when getting filter options: {e}") from e

        finally:
            if conn is not None and self._pool is not None:
                self._pool.putconn(conn)

    def _build_sql_query(self, query: QueryRequest) -> tuple[str, dict[str, Any]]:
        """Build a SQL query from a QueryRequest.

        Args:
            query: The query request

        Returns:
            Tuple of SQL string and parameters
        """
        source = f'"{query.table_name}"'
        select: list[str] = []
        where_parts: list[str] = []
        order_by_parts: list[str] = []
        params: dict[str, Any] = {}
        param_idx = 0

        for s in query.select:
            select.append(f'"{s.column_name}" AS "{s.alias or s.column_name}"')

            # Add to group by if needed
            # if query.breakdown is not None:
            #     group_by_parts.append(f'"{column_name}"')

        for a in query.aggregations:
            if isinstance(a, QueryRequestAggregation):
                select.append(f'{a.aggregation_function}("{a.column_name}") AS "{a.alias}"')
            elif isinstance(a, QueryRequestCustomAggregation):
                select.append(f'{a.aggregation_function} AS "{a.alias}"')

        for f in query.filters:
            if f.kind == "QueryRequestFilterCategory" and f.values:
                param_name = f"p{param_idx}"
                where_parts.append(f'"{f.column_name}" IN (%({param_name})s)')
                params[param_name] = f"{','.join(f.values)}"
                param_idx += 1
            elif f.kind == "QueryRequestFilterFact" and f.values:
                min_val, max_val = f.values

                if min_val is not None:
                    param_name = f"p{param_idx}"
                    where_parts.append(f'"{f.column_name}" >= %({param_name})s')
                    params[param_name] = min_val
                    param_idx += 1

                if max_val is not None:
                    param_name = f"p{param_idx}"
                    where_parts.append(f'"{f.column_name}" <= %({param_name})s')
                    params[param_name] = max_val  # This is a single value, not a list
                    param_idx += 1

        # Process order by
        for order in query.order_by:
            if isinstance(order, tuple):
                col, direction = order
                order_by_parts.append(f'"{col}" {direction}')
            else:
                order_by_parts.append(f'"{order.column_name}" {order.direction}')

        # Process pagination
        limit = None
        offset = None

        if isinstance(query.pagination, tuple):
            offset, limit = query.pagination
        else:
            offset = query.pagination.offset
            limit = query.pagination.limit

        # Build the final SQL
        sql = f"""
        SELECT {", ".join(select) or "*"} FROM {source}
        """

        if where_parts:
            sql += f" WHERE {' AND '.join(where_parts)}"

        if query.group_by:
            sql += f" GROUP BY {', '.join(query.group_by)}"

        if order_by_parts:
            sql += f" ORDER BY {', '.join(order_by_parts)}"

        if limit is not None:
            sql += f" LIMIT {limit}"

        if offset is not None:
            sql += f" OFFSET {offset}"

        return sql, params

    def _get_category_filter_options(self, cursor) -> list[FilterOptionCategory]:
        """Get filter options for category columns.

        Args:
            cursor: Database cursor

        Returns:
            List of category filter options
        """
        # This is a placeholder implementation
        # In a real scenario, you would query the database for distinct values in category columns
        options: list[FilterOptionCategory] = []

        # Example SQL to get distinct values for each category column
        # For each table and column combination marked as Category in the dataset
        # SELECT DISTINCT column_name FROM table_name ORDER BY column_name

        return options

    def _get_numeric_filter_options(self, cursor) -> list[FilterOptionMinMax]:
        """Get filter options for numeric columns.

        Args:
            cursor: Database cursor

        Returns:
            List of numeric filter options
        """
        # This is a placeholder implementation
        # In a real scenario, you would query the database for min/max values of numeric columns
        options: list[FilterOptionMinMax] = []

        # Example SQL to get min/max values for each numeric column
        # For each table and column combination marked as Fact in the dataset
        # SELECT MIN(column_name), MAX(column_name) FROM table_name

        return options
