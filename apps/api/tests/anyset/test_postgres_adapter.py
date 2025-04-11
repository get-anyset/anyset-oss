"""Tests for the PostgreSQL adapter."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
from psycopg2.extras import RealDictCursor
import pytest

from anyset.models import ColumnType, RepositoryOption
from anyset.postgres_adapter.adapter import PostgresAdapter


@pytest.fixture
def adapter_config():
    """PostgreSQL settings fixture."""
    return {
        "host": "localhost",
        "port": 5432,
        "user": "test",
        "password": "test",
        "database": "test",
        "pool_min_size": 1,
        "pool_max_size": 10,
        "query_timeout": 30,
    }


@pytest.fixture
def adapter():
    """PostgreSQL adapter fixture."""
    return RepositoryOption.postgresql


@pytest.fixture
def mock_cursor():
    """Create a mock cursor."""
    cursor = MagicMock(spec=RealDictCursor)
    cursor.description = [
        ("n", None, None),
        ("k", None, None),
        ("v", None, None),
    ]
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    """Create a mock connection."""
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = mock_cursor
    return connection


@pytest.fixture
def mock_pool(mock_connection):
    """Create a mock connection pool."""
    pool = MagicMock()
    pool.getconn.return_value = mock_connection
    return pool


@pytest.fixture
def adapter_instance(mock_dataset, mock_pool, adapter_config):
    """Create a mock adapter with mocked connection pool."""
    with (
        patch("anyset.postgres_adapter.adapter.PostgresSettings") as mock_settings,
        patch("psycopg2.pool.SimpleConnectionPool") as mock_pool_class,
    ):
        mock_settings.return_value = MagicMock(**adapter_config)
        mock_pool_class.return_value = mock_pool
        adapter = PostgresAdapter(dataset=mock_dataset)
        return adapter


@pytest.mark.asyncio
async def test_get_filter_options(adapter_instance, mock_cursor):
    """Test get_filter_options method."""
    # Mock cursor results for simple filter options
    mock_cursor.fetchall.side_effect = [
        [
            {
                "n": "category_col",
                "k": ColumnType.text_category.value,
                "v": ["value1", "value2"],
            },
            {
                "n": "fact_col",
                "k": ColumnType.numeric_fact.value,
                "v": ["0.0", "100.0"],
            },
            {
                "n": "datetime_col",
                "k": ColumnType.datetime.value,
                "v": ["2023-01-01T00:00:00", "2023-12-31T23:59:59"],
            },
            {
                "n": "boolean_col",
                "k": ColumnType.boolean.value,
                "v": ["true", "false"],
            },
        ],
        [
            {
                "test_table.category_col": "parent1",
                "test_table.fact_col": "child1",
            },
            {
                "test_table.category_col": "parent1",
                "test_table.fact_col": "child2",
            },
            {
                "test_table.category_col": "parent2",
                "test_table.fact_col": "child3",
            },
        ],
    ]

    # Execute
    result = await adapter_instance.get_filter_options()

    # Verify
    assert len(result) == 5  # 4 simple filters + 1 hierarchy
    assert result[0].name == "category_col"
    assert result[0].kind == "CategoricalFilterOption"
    assert result[0].values == ["value1", "value2"]

    assert result[1].name == "fact_col"
    assert result[1].kind == "MinMaxFilterOption"
    assert result[1].values == (0.0, 100.0)

    assert result[2].name == "datetime_col"
    assert result[2].kind == "MinMaxFilterOption"
    assert result[2].values == (
        datetime.fromisoformat("2023-01-01T00:00:00"),
        datetime.fromisoformat("2023-12-31T23:59:59"),
    )

    assert result[3].name == "boolean_col"
    assert result[3].kind == "CategoricalFilterOption"
    assert result[3].values == [True, False]

    # Verify hierarchy
    assert result[4].name == "test_hierarchy"
    assert len(result[4].values) == 2  # Two parent values
    assert result[4].values[0][0] == "parent1"
    assert result[4].values[1][0] == "parent2"
    assert len(result[4].values[0][1].values) == 2  # Two children for parent1
    assert len(result[4].values[1][1].values) == 1  # One child for parent2


@pytest.mark.asyncio
async def test_get_filter_options_hierarchical(adapter_instance, mock_cursor):
    """Test get_filter_options with hierarchical data."""
    # Mock cursor results
    mock_cursor.fetchall.side_effect = [
        [],  # Empty result for simple filter options
        [
            {
                "test_table.category_col": "parent1",
                "test_table.fact_col": "child1",
            },
            {
                "test_table.category_col": "parent1",
                "test_table.fact_col": "child2",
            },
            {
                "test_table.category_col": "parent2",
                "test_table.fact_col": "child3",
            },
        ],
    ]

    # Execute
    result = await adapter_instance.get_filter_options()

    # Verify hierarchical structure
    assert len(result) == 1
    assert result[0].name == "test_hierarchy"
    assert len(result[0].values) == 2  # Two parent values
    assert result[0].values[0][0] == "parent1"
    assert result[0].values[1][0] == "parent2"
    assert len(result[0].values[0][1].values) == 2  # Two children for parent1
    assert len(result[0].values[1][1].values) == 1  # One child for parent2


@pytest.mark.asyncio
async def test_get_filter_options_empty(adapter_instance, mock_cursor):
    """Test get_filter_options with no data."""
    # Mock empty cursor results for both queries
    mock_cursor.fetchall.side_effect = [[], []]

    # Execute
    result = await adapter_instance.get_filter_options()

    # Verify
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_filter_options_error(adapter_instance, mock_pool):
    """Test get_filter_options error handling."""
    # Mock connection error
    error = Exception("Connection error")
    mock_pool.getconn.side_effect = error

    # Execute and verify
    with pytest.raises(Exception) as exc_info:
        await adapter_instance.get_filter_options()
    assert str(error) == str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "column_type,values,expected",
    [
        (ColumnType.text_category, ["value1", "value2"], ["value1", "value2"]),
        (ColumnType.boolean, ["true", "false"], [True, False]),
        (
            ColumnType.datetime,
            ["2023-01-01T00:00:00", "2023-12-31T23:59:59"],
            [
                datetime.fromisoformat("2023-01-01T00:00:00"),
                datetime.fromisoformat("2023-12-31T23:59:59"),
            ],
        ),
        (ColumnType.numeric_fact, ["0.0", "100.0"], [0.0, 100.0]),
    ],
)
async def test_process_filter_options(adapter_instance, column_type, values, expected):
    """Test _process_filter_options method with different column types."""
    # Execute
    result = adapter_instance._process_filter_options(
        {
            "k": column_type.value,
            "v": values,
        }
    )

    # Verify
    assert result == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "column_name, column_type, expected_sql_pattern",
    [
        (
            "category_col_a",
            ColumnType.text_category,
            "ARRAY_AGG(DISTINCT category_col_a::varchar)",
        ),
        (
            "fact_col",
            ColumnType.numeric_fact,
            "ARRAY[MIN(fact_col::varchar), MAX(fact_col::varchar)]",
        ),
        (
            "datetime_col",
            ColumnType.datetime,
            "ARRAY[MIN(datetime_col::varchar), MAX(datetime_col::varchar)]",
        ),
        (
            "boolean_col",
            ColumnType.boolean,
            "ARRAY_AGG(DISTINCT boolean_col::varchar)",
        ),
    ],
)
async def test_create_simple_filter_options_statement(
    adapter_instance,
    column_name,
    column_type,
    expected_sql_pattern,
):
    """Test _create_simple_filter_options_statement with different column types."""
    # Execute
    result = adapter_instance._create_simple_filter_options_statement(
        "test_table",
        column_name,
    )

    # Verify
    assert expected_sql_pattern in result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hierarchy_data,expected_structure",
    [
        (
            {
                "test_table.category_col": ["parent1", "parent1", "parent2"],
                "test_table.fact_col": ["child1", "child2", "child3"],
            },
            {
                "name": "test_table.category_col",
                "values_count": 2,
                "first_parent": "parent1",
                "second_parent": "parent2",
                "children_count": 2,
            },
        ),
        (
            {
                "test_table.category_col": ["parent1", "parent2", "parent3"],
                "test_table.fact_col": ["child1", "child2", "child3"],
            },
            {
                "name": "test_table.category_col",
                "values_count": 3,
                "first_parent": "parent1",
                "second_parent": "parent2",
                "children_count": 1,
            },
        ),
    ],
)
async def test_walk_hierarchy(adapter_instance, hierarchy_data, expected_structure):
    """Test _walk_hierarchy with different hierarchical structures."""
    # Create sample data
    data = pd.DataFrame(hierarchy_data)

    # Execute
    result = adapter_instance._walk_hierarchy(
        data, ["test_table.category_col", "test_table.fact_col"]
    )

    # Verify
    assert result.name == expected_structure["name"]
    assert len(result.values) == expected_structure["values_count"]
    assert result.values[0][0] == expected_structure["first_parent"]
    assert result.values[1][0] == expected_structure["second_parent"]
    assert hasattr(result.values[0][1], "values")  # Check if it's a FilterOptions-like object
    assert len(result.values[0][1].values) == expected_structure["children_count"]


@pytest.mark.asyncio
async def test_get_filter_options_no_pool(mock_dataset):
    """Test get_filter_options when pool is not initialized."""
    # Create adapter without pool
    adapter = PostgresAdapter(dataset=mock_dataset)

    # Execute and verify
    with pytest.raises(RuntimeError) as exc_info:
        await adapter.get_filter_options()
    assert "PostgreSQLConnectionPoolNotInitialized" == str(exc_info.value)
