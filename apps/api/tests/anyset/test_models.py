"""Tests for the AnySet models."""

import pytest

from anyset.models import (
    BaseModel,
    BaseQueryRequest,
    BaseResultset,
    BaseResultsetColumn,
    CategoricalFilterOption,
    ColumnType,
    Dataset,
    DatasetTable,
    DatasetTableColumn,
    MinMaxFilterOption,
    QueryRequestAggregation,
    QueryRequestFilterCategory,
    QueryRequestFilterFact,
    QueryRequestOrderBy,
    QueryRequestPagination,
    QueryRequestSelect,
    RepositoryOption,
)


def test_base_model_id_generation():
    """Test the ID generation in BaseModel."""
    model = BaseModel(kind="Test", name="Test Model", description="Test Description")
    assert model._id == "test-test-model"


def test_dataset_table_column():
    """Test DatasetTableColumn model."""
    column = DatasetTableColumn(
        name="test_column",
        column_type=ColumnType.text_category,
    )
    assert column.kind == "DatasetTableColumn"
    assert column.name == "test_column"
    assert column.column_type == ColumnType.text_category


def test_dataset_table():
    """Test DatasetTable model."""
    column = DatasetTableColumn(
        name="test_column",
        column_type=ColumnType.text_category,
    )
    table = DatasetTable(name="test_table", columns={"test_column": column})
    assert table.kind == "DatasetTable"
    assert table.name == "test_table"
    assert "test_column" in table.columns
    assert table.columns["test_column"].name == "test_column"


def test_dataset_column_classification():
    """Test Dataset column classification methods."""
    category_column = DatasetTableColumn(
        name="category_col",
        column_type=ColumnType.text_category,
    )
    datetime_column = DatasetTableColumn(
        name="datetime_col",
        column_type=ColumnType.datetime,
    )
    fact_column = DatasetTableColumn(
        name="fact_col",
        column_type=ColumnType.numeric_fact,
    )
    other_column = DatasetTableColumn(
        name="other_col",
        column_type=ColumnType.text_other,
    )

    table = DatasetTable(
        name="test_table",
        columns={
            "category_col": category_column,
            "datetime_col": datetime_column,
            "fact_col": fact_column,
            "other_col": other_column,
        },
    )

    dataset = Dataset(
        name="test_dataset",
        path_prefix="/test",
        version=1,
        database_name="test_db",
        dataset_tables={"test_table": table},
        adapter=RepositoryOption.in_memory,
    )

    assert "category_col" in dataset.dataset_cols_text_category["test_table"]
    assert "datetime_col" in dataset.dataset_cols_datetime["test_table"]
    assert "fact_col" in dataset.dataset_cols_numeric_fact["test_table"]
    assert "other_col" in dataset.dataset_cols_text_other["test_table"]

    assert dataset.is_col_classified_as("category_col", ColumnType.text_category, "test_table")
    assert dataset.is_col_classified_as("datetime_col", ColumnType.datetime, "test_table")
    assert dataset.is_col_classified_as("fact_col", ColumnType.numeric_fact, "test_table")
    assert dataset.is_col_classified_as("other_col", ColumnType.text_other, "test_table")

    # Test invalid column type
    with pytest.raises(ValueError):
        dataset.is_col_classified_as("invalid_col", ColumnType.text_category, "invalid_table")


def test_query_request_models():
    """Test query request related models."""
    # Test QueryRequestFilterCategory
    category_filter = QueryRequestFilterCategory(
        column_name="test_col", values=["value1", "value2"]
    )
    assert category_filter.kind == "QueryRequestFilterCategory"
    assert category_filter.column_name == "test_col"
    assert category_filter.values == ["value1", "value2"]

    # Test QueryRequestFilterFact
    fact_filter = QueryRequestFilterFact(column_name="test_col", values=(0.0, 100.0))
    assert fact_filter.kind == "QueryRequestFilterFact"
    assert fact_filter.column_name == "test_col"
    assert fact_filter.values == (0.0, 100.0)

    # Test QueryRequestSelect
    select = QueryRequestSelect(column_name="test_col", alias="test_alias")
    assert select.kind == "QueryRequestSelect"
    assert select.column_name == "test_col"
    assert select.alias == "test_alias"


def test_base_query_request():
    """Test BaseQueryRequest model."""
    query = BaseQueryRequest(
        table_name="test_table",
        filters=[QueryRequestFilterCategory(column_name="test_col", values=["value1"])],
        select=[QueryRequestSelect(column_name="test_col", alias="test_alias")],
        aggregations=[
            QueryRequestAggregation(
                column_name="test_col",
                aggregation_function="COUNT",
                alias="count_alias",
            )
        ],
        order_by=[QueryRequestOrderBy(column_name="test_col", direction="ASC")],
        pagination=QueryRequestPagination(limit=10, offset=0),
        breakdown="test_col",
    )

    assert query.table_name == "test_table"
    assert len(query.filters) == 1
    assert len(query.select) == 1
    assert len(query.aggregations) == 1
    assert len(query.order_by) == 1
    assert query.pagination.limit == 10
    assert query.breakdown == "test_col"

    # Test group_by computation
    group_by = query.group_by
    assert "test_alias" in group_by  # from select
    assert "test_col" in group_by  # from order_by and breakdown


def test_base_resultset():
    """Test BaseResultset model."""
    column = BaseResultsetColumn(alias="test_col", data=["value1", "value2"])

    resultset = BaseResultset(dataset="test_dataset", version=1, rows=2, columns=[column])

    assert resultset.dataset == "test_dataset"
    assert resultset.version == 1
    assert resultset.rows == 2
    assert len(resultset.columns) == 1
    assert resultset.columns[0].alias == "test_col"


def test_filter_option_models():
    """Test filter option related models."""
    # Test MinMaxFilterOption
    min_max = MinMaxFilterOption(name="test_minmax", values=(0.0, 100.0))
    assert min_max.kind == "MinMaxFilterOption"
    assert min_max.name == "test_minmax"
    assert min_max.values[0] == 0.0
    assert min_max.values[1] == 100.0

    # Test CategoricalFilterOption
    category = CategoricalFilterOption(name="test_category", values=["value1", "value2"])
    assert category.kind == "CategoricalFilterOption"
    assert category.name == "test_category"
    assert len(category.values) == 2
