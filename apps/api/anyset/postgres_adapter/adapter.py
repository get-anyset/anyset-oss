"""PostgreSQL adapter for the AnySet repository."""

import logging
from typing import Any, cast

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

# Local application imports
from ..models import (
    FilterOptionCategory,
    FilterOptionMinMax,
    QueryRequest,
    QueryRequestAggregation,
    QueryRequestCustomAggregation,
    QueryRequestSelect,
)
from ..models import (
    FilterOptionsDTO as FilterOptions,
)
from ..models import (
    QueryResponseDTO as QueryResponse,
)
from ..repository import RepositoryPort
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

    async def execute_query(self, query: QueryRequest) -> QueryResponse:
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

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                columns = [desc[0] for desc in cursor.description]

                return QueryResponse(
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

            return cast(FilterOptions, filter_options)

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
        # Start building the SQL query
        select_parts: list[str] = []
        from_part = f'"{query.table_name}"'
        where_parts: list[str] = []
        group_by_parts: list[str] = []
        order_by_parts: list[str] = []
        params: dict[str, Any] = {}
        param_idx = 0

        # Process select fields - handle both normalized and non-normalized selects
        select_fields: list[QueryRequestSelect] = []
        for select in query.select:
            if isinstance(select, str):
                select_fields.append(
                    QueryRequestSelect(kind="QueryRequestSelect", column_name=select, alias=select)
                )
            elif isinstance(select, tuple):
                select_fields.append(
                    QueryRequestSelect(
                        kind="QueryRequestSelect", column_name=select[0], alias=select[1]
                    )
                )
            elif isinstance(select, QueryRequestSelect):
                select_fields.append(select)

        for select_field in select_fields:
            column_name = select_field.column_name
            alias = select_field.alias or column_name
            select_parts.append(f'"{column_name}" AS "{alias}"')

            # Add to group by if needed
            if query.breakdown is not None:
                group_by_parts.append(f'"{column_name}"')

        # Process aggregations
        for agg in query.aggregations:
            if isinstance(agg, QueryRequestAggregation):
                # Standard aggregation
                column_name = agg.column_name
                agg_func = agg.aggregation_function
                alias = agg.alias
                select_parts.append(f'{agg_func}("{column_name}") AS "{alias}"')
            elif isinstance(agg, QueryRequestCustomAggregation):
                # Custom aggregation
                select_parts.append(f'{agg.aggregation_function} AS "{agg.alias}"')
            elif isinstance(agg, tuple) and len(agg) == 3:
                # Handle tuple[str, AggregationFunction, str]
                column_name, agg_func, alias = agg
                select_parts.append(f'{agg_func}("{column_name}") AS "{alias}"')
            elif isinstance(agg, tuple) and len(agg) == 2:
                # Handle tuple[str, str] for custom aggregation
                agg_func, alias = agg
                select_parts.append(f'{agg_func} AS "{alias}"')

        # Process filters
        for filter in query.filters:
            if filter.kind == "QueryRequestFilterCategory":
                # Category filter
                col_name = filter.column_name
                if filter.values:
                    param_name = f"p{param_idx}"
                    where_parts.append(f'"{col_name}" = ANY(%({param_name})s)')
                    params[param_name] = filter.values
                    param_idx += 1
            elif filter.kind == "QueryRequestFilterFact":
                # Fact filter (numeric range)
                col_name = filter.column_name
                min_val, max_val = filter.values

                if min_val is not None:
                    param_name = f"p{param_idx}"
                    where_parts.append(f'"{col_name}" >= %({param_name})s')
                    params[param_name] = min_val  # This is a single value, not a list
                    param_idx += 1

                if max_val is not None:
                    param_name = f"p{param_idx}"
                    where_parts.append(f'"{col_name}" <= %({param_name})s')
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
        sql = f"SELECT {', '.join(select_parts) or '*'} FROM {from_part}"

        if where_parts:
            sql += f" WHERE {' AND '.join(where_parts)}"

        if group_by_parts:
            sql += f" GROUP BY {', '.join(group_by_parts)}"

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
