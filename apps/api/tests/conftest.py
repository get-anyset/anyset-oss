"""Test configuration."""

from pathlib import Path
import sys

import pytest

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from anyset.models import (
    ColumnType,
    Dataset,
    DatasetTable,
    DatasetTableColumn,
    RepositoryOption,
)


@pytest.fixture
def mock_dataset(adapter: RepositoryOption, adapter_config: dict):
    """Create a sample dataset for testing."""
    category_column_a = DatasetTableColumn(
        name="category_col_a",
        column_type=ColumnType.text_category,
    )
    category_column_b = DatasetTableColumn(
        name="category_col_b",
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
    boolean_column = DatasetTableColumn(
        name="boolean_col",
        column_type=ColumnType.boolean,
    )

    table = DatasetTable(
        name="test_table",
        columns={
            "category_col_a": category_column_a,
            "category_col_b": category_column_b,
            "fact_col": fact_column,
            "datetime_col": datetime_column,
            "boolean_col": boolean_column,
        },
    )

    return Dataset(
        name="Test Dataset",
        path_prefix="/test-dataset",
        version=1,
        dataset_tables={"test_table": table},
        adapter=adapter,
        adapter_config=adapter_config,
        category_hierarchies={
            "test_hierarchy": [
                ("test_table", "category_col_a"),
                ("test_table", "category_col_b"),
            ]
        },
    )
