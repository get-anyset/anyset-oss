"""Tests for the AnySet repository module."""

from fastapi import HTTPException, status
import pytest

from anyset.models import (
    BuiltInRepositoryAdapter,
    ColumnDataType,
    ColumnType,
    Dataset,
    DatasetTable,
    DatasetTableColumn,
    QueryRequest,
    QueryRequestAggregation,
    QueryRequestCustomAggregation,
    QueryRequestFilterCategory,
    QueryRequestFilterFact,
    QueryRequestOrderBy,
    QueryRequestPagination,
    QueryRequestSelect,
)
from anyset.repository_interface import IRepository


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    category_column = DatasetTableColumn(
        name="category_col",
        column_type=ColumnType.Category,
        column_data_type=ColumnDataType.String,
    )
    fact_column = DatasetTableColumn(
        name="fact_col",
        column_type=ColumnType.Fact,
        column_data_type=ColumnDataType.Number,
    )
    datetime_column = DatasetTableColumn(
        name="datetime_col",
        column_type=ColumnType.DateTime,
        column_data_type=ColumnDataType.DateTime,
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
        database_name="test_db",
        dataset_tables={"test_table": table},
        adapter=BuiltInRepositoryAdapter.InMemory,
        custom_aggregation_functions={"custom_sum": "SUM"},
    )


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
    # Test that IRepository is abstract
    with pytest.raises(TypeError):
        IRepository()

    # Test that abstract methods are not implemented
    class ConcreteRepository(IRepository):
        pass

    with pytest.raises(TypeError):
        ConcreteRepository()
