"""Tests for the AnySet repository module."""

from unittest.mock import AsyncMock

from fastapi import HTTPException, status
import pytest

from anyset.models import (
    BaseResultsetColumn,
    CategoricalFilterOption,
    ColumnType,
    Dataset,
    DatasetTable,
    DatasetTableColumn,
    FilterOptions,
    MinMaxFilterOption,
    QueryRequest,
    QueryRequestAggregation,
    QueryRequestCustomAggregation,
    QueryRequestFilterCategory,
    QueryRequestFilterFact,
    QueryRequestOrderBy,
    QueryRequestPagination,
    QueryRequestSelect,
    RepositoryOption,
    Resultset,
)
from anyset.repository_interface import IRepository


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    category_column = DatasetTableColumn(
        name="category_col",
        column_type=ColumnType.text_category,
    )
    fact_column = DatasetTableColumn(
        name="fact_col",
        column_type=ColumnType.numeric_fact,
    )
    datetime_column = DatasetTableColumn(
        name="datetime_col",
        column_type=ColumnType.datetime,
    )

    table = DatasetTable(
        name="test_table",
        columns={
            "category_col": category_column,
            "fact_col": fact_column,
            "datetime_col": datetime_column,
        },
    )

    return Dataset(
        name="test_dataset",
        path_prefix="/test",
        version=1,
        dataset_tables={"test_table": table},
        adapter=RepositoryOption.in_memory,
        custom_aggregation_functions={"custom_sum": "SUM"},
    )


@pytest.fixture
def sample_query_request(sample_dataset):
    """Create a sample query request for testing."""
    return QueryRequest(
        table_name="test_table",
        dataset=sample_dataset,
        filters=[
            QueryRequestFilterCategory(
                column_name="category_col",
                values=["value1", "value2"],
            ),
            QueryRequestFilterFact(
                column_name="fact_col",
                values=(0.0, 100.0),
            ),
        ],
        select=[
            QueryRequestSelect(
                column_name="category_col",
                alias="category",
            ),
            QueryRequestSelect(
                column_name="fact_col",
                alias="fact",
            ),
        ],
        aggregations=[
            QueryRequestAggregation(
                column_name="fact_col",
                aggregation_function="COUNT",
                alias="count",
            ),
        ],
        order_by=[
            QueryRequestOrderBy(
                column_name="category_col",
                direction="ASC",
            ),
        ],
        pagination=QueryRequestPagination(
            limit=10,
            offset=0,
        ),
    )


@pytest.fixture
def sample_resultset(sample_dataset):
    """Create a sample resultset for testing."""
    return Resultset(
        dataset=sample_dataset._id,
        version=sample_dataset.version,
        rows=2,
        columns=[
            BaseResultsetColumn(
                alias="category",
                breakdown=None,
                data=["value1", "value2"],
            ),
            BaseResultsetColumn(
                alias="fact",
                breakdown=None,
                data=[10.5, 20.7],
            ),
            BaseResultsetColumn(
                alias="count",
                breakdown=None,
                data=[5, 8],
            ),
        ],
    )


@pytest.fixture
def sample_filter_options():
    """Create sample filter options for testing."""
    return [
        CategoricalFilterOption(name="category_col", values=["value1", "value2"]),
        MinMaxFilterOption(name="fact_col", values=(0.0, 100.0)),
    ]


def test_query_request_validation(sample_dataset):
    """Test QueryRequest validation."""
    # Test valid query request
    query = QueryRequest(
        table_name="test_table",
        dataset=sample_dataset,
        filters=[
            QueryRequestFilterCategory(
                column_name="category_col",
                values=["value1", "value2"],
            ),
            QueryRequestFilterFact(
                column_name="fact_col",
                values=(0.0, 100.0),
            ),
        ],
        select=[
            QueryRequestSelect(
                column_name="category_col",
                alias="category",
            ),
            QueryRequestSelect(
                column_name="fact_col",
                alias="fact",
            ),
        ],
        aggregations=[
            QueryRequestAggregation(
                column_name="fact_col",
                aggregation_function="COUNT",
                alias="count",
            ),
            QueryRequestCustomAggregation(
                aggregation_function="custom_sum",
                alias="sum",
            ),
        ],
        order_by=[
            QueryRequestOrderBy(
                column_name="category_col",
                direction="ASC",
            ),
        ],
        pagination=QueryRequestPagination(
            limit=10,
            offset=0,
        ),
    )
    assert query.kind == "QueryRequest"
    assert query.table_name == "test_table"
    assert len(query.filters) == 2
    assert len(query.select) == 2
    assert len(query.aggregations) == 2
    assert len(query.order_by) == 1

    # Test invalid table name
    with pytest.raises(HTTPException) as exc_info:
        QueryRequest(
            table_name="invalid_table",
            dataset=sample_dataset,
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "TableNotFound dataset-test-dataset:invalid_table"

    # Test invalid category filter column
    with pytest.raises(HTTPException) as exc_info:
        QueryRequest(
            table_name="test_table",
            dataset=sample_dataset,
            filters=[
                QueryRequestFilterCategory(
                    column_name="fact_col",  # Using fact column for category filter
                    values=["value1"],
                ),
            ],
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "QueryRequestFilterCategoryInvalidColumn fact_col"

    # Test invalid fact filter column
    with pytest.raises(HTTPException) as exc_info:
        QueryRequest(
            table_name="test_table",
            dataset=sample_dataset,
            filters=[
                QueryRequestFilterFact(
                    column_name="category_col",  # Using category column for fact filter
                    values=(0.0, 100.0),
                ),
            ],
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "QueryRequestFilterFactInvalidColumn category_col"

    # Test invalid select column
    with pytest.raises(HTTPException) as exc_info:
        QueryRequest(
            table_name="test_table",
            dataset=sample_dataset,
            select=[
                QueryRequestSelect(
                    column_name="invalid_col",
                    alias="invalid",
                ),
            ],
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "SelectColumnNotFound invalid_col"

    # Test invalid aggregation column
    with pytest.raises(HTTPException) as exc_info:
        QueryRequest(
            table_name="test_table",
            dataset=sample_dataset,
            aggregations=[
                QueryRequestAggregation(
                    column_name="category_col",  # Using category column for fact aggregation
                    aggregation_function="COUNT",
                    alias="count",
                ),
            ],
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "AggregationColumnNotFound category_col"

    # Test invalid custom aggregation function
    with pytest.raises(HTTPException) as exc_info:
        QueryRequest(
            table_name="test_table",
            dataset=sample_dataset,
            aggregations=[
                QueryRequestCustomAggregation(
                    aggregation_function="invalid_function",
                    alias="invalid",
                ),
            ],
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "CustomAggregationFunctionNotFound invalid_function"

    # Test invalid pagination
    with pytest.raises(HTTPException) as exc_info:
        QueryRequest(
            table_name="test_table",
            dataset=sample_dataset,
            pagination=QueryRequestPagination(
                limit=0,  # Invalid limit
                offset=0,
            ),
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "InvalidPaginationParameters" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        QueryRequest(
            table_name="test_table",
            dataset=sample_dataset,
            pagination=QueryRequestPagination(
                limit=10,
                offset=-1,  # Invalid offset
            ),
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "InvalidPaginationParameters" in exc_info.value.detail


def test_repository_port():
    """Test IRepository abstract class."""
    # Test that IRepository is abstract and can't be instantiated directly

    # Verify that IRepository has abstract methods by checking decorators

    # Check that execute_query is an abstract method
    assert hasattr(
        IRepository,
        "execute_query",
    ), "IRepository should have method execute_query "
    method = IRepository.execute_query
    assert getattr(
        method,
        "__isabstractmethod__",
        False,
    ), "execute_query method should be abstract"

    # Check that get_filter_options is an abstract method
    assert hasattr(
        IRepository,
        "get_filter_options",
    ), "IRepository should have method get_filter_options"
    method = IRepository.get_filter_options
    assert getattr(
        method,
        "__isabstractmethod__",
        False,
    ), "get_filter_options method should be abstract"


class MockRepository(IRepository):
    """Mock implementation of IRepository for testing."""

    def __init__(self):
        """Initialize the mock repository."""
        self.execute_query_mock = AsyncMock()
        self.get_filter_options_mock = AsyncMock()

    async def execute_query(self, query: QueryRequest) -> Resultset:
        """Mock execute_query method."""
        return await self.execute_query_mock(query)

    async def get_filter_options(self) -> FilterOptions:
        """Mock get_filter_options method."""
        return await self.get_filter_options_mock()


@pytest.mark.asyncio
async def test_execute_query(sample_query_request, sample_resultset):
    """Test execute_query method."""
    # Setup
    repo = MockRepository()
    repo.execute_query_mock.return_value = sample_resultset

    # Execute
    result = await repo.execute_query(sample_query_request)

    # Verify
    repo.execute_query_mock.assert_called_once_with(sample_query_request)
    assert result == sample_resultset
    assert result.rows == 2
    assert len(result.columns) == 3
    assert result.columns[0].alias == "category"
    assert result.columns[1].alias == "fact"
    assert result.columns[2].alias == "count"


@pytest.mark.asyncio
async def test_get_filter_options(sample_filter_options):
    """Test get_filter_options method."""
    # Setup
    repo = MockRepository()
    repo.get_filter_options_mock.return_value = sample_filter_options

    # Execute
    result = await repo.get_filter_options()

    # Verify
    repo.get_filter_options_mock.assert_called_once()
    assert result == sample_filter_options
    assert len(result) == 2

    # Check first filter option (category type)
    assert result[0].kind == "CategoricalFilterOption"
    assert len(result[0].values) == 2
    assert result[0].values[0] == "value1"
    assert result[0].values[1] == "value2"

    # Check second filter option (min/max type)
    assert result[1].kind == "MinMaxFilterOption"
    assert result[1].values[0] == 0.0
    assert result[1].values[1] == 100.0


@pytest.mark.parametrize(
    "exception,expected_error",
    [
        (RuntimeError("Database error"), "Database error"),
        (ConnectionError("Connection failed"), "Connection failed"),
        (ValueError("Invalid value"), "Invalid value"),
    ],
)
@pytest.mark.asyncio
async def test_execute_query_exception_handling(sample_query_request, exception, expected_error):
    """Test execute_query method exception handling."""
    # Setup
    repo = MockRepository()
    repo.execute_query_mock.side_effect = exception

    # Execute and verify
    with pytest.raises(type(exception)) as exc_info:
        await repo.execute_query(sample_query_request)

    assert str(exc_info.value) == expected_error
    repo.execute_query_mock.assert_called_once_with(sample_query_request)


@pytest.mark.parametrize(
    "exception,expected_error",
    [
        (RuntimeError("Database error"), "Database error"),
        (ConnectionError("Connection failed"), "Connection failed"),
        (ValueError("Invalid value"), "Invalid value"),
    ],
)
@pytest.mark.asyncio
async def test_get_filter_options_exception_handling(exception, expected_error):
    """Test get_filter_options method exception handling."""
    # Setup
    repo = MockRepository()
    repo.get_filter_options_mock.side_effect = exception

    # Execute and verify
    with pytest.raises(type(exception)) as exc_info:
        await repo.get_filter_options()

    assert str(exc_info.value) == expected_error
    repo.get_filter_options_mock.assert_called_once()


@pytest.mark.asyncio
async def test_abstract_execute_query_raises_not_implemented():
    """Test that IRepository.execute_query raises NotImplementedError when not implemented."""

    class ConcreteRepository(IRepository):
        async def get_filter_options(self):
            pass  # implement one method but not execute_query

    repo = ConcreteRepository(dataset=sample_dataset)
    with pytest.raises(NotImplementedError) as exc_info:
        await repo.execute_query(None)
    assert "MethodNotImplementedBySubClass execute_query" in str(exc_info.value)


@pytest.mark.asyncio
async def test_abstract_get_filter_options_raises_not_implemented():
    """Test that IRepository.get_filter_options raises NotImplementedError when not implemented."""

    class ConcreteRepository(IRepository):
        async def execute_query(self, query):
            pass  # implement one method but not get_filter_options

    repo = ConcreteRepository(dataset=sample_dataset)
    with pytest.raises(NotImplementedError) as exc_info:
        await repo.get_filter_options()
    assert "MethodNotImplementedBySubClass get_filter_options" in str(exc_info.value)
