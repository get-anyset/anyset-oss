"""Models for the AnySet Framework."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel as PydanticBaseModel
from pydantic import computed_field
from slugify import slugify


class BaseModel(PydanticBaseModel):
    """Base properties for all models."""

    kind: str
    name: str
    description: str | None = None

    @computed_field
    @property
    def _id(self) -> str:
        """The ID of the model."""
        return slugify(f"{self.kind} {self.name}")

    # model_config = {
    #     "json_schema_extra": {
    #         "examples": [
    #             {
    #                 "kind": "Application",
    #                 "Id": "app-123",
    #                 "Name": "Sample App",
    #                 "description": "A sample application",
    #             }
    #         ]
    #     }
    # }


class ColumnType(str, Enum):
    """The class of a column."""

    Category = "Category"
    DateTime = "DateTime"
    Fact = "Fact"
    Other = "Other"


class ColumnDataType(str, Enum):
    """The data type of a column."""

    String = "String"
    Number = "Number"
    Boolean = "Boolean"
    DateTime = "DateTime"


class DatasetTableColumn(BaseModel):
    """A column in a table."""

    kind: Literal["DatasetTableColumn"] = "DatasetTableColumn"
    column_type: ColumnType
    column_data_type: ColumnDataType


class DatasetTable(BaseModel):
    """A table in a dataset."""

    kind: Literal["DatasetTable"] = "DatasetTable"
    columns: dict[str, DatasetTableColumn]


class Dataset(BaseModel):
    """A dataset is a collection of data tables."""

    kind: Literal["Dataset"] = "Dataset"
    path_prefix: str
    version: int
    dataset_tables: dict[str, DatasetTable]

    @computed_field
    @property
    def _DatasetColumnsCategory(self) -> dict[str, list[str]]:
        """Dictionary of table names and their category columns."""
        return {
            t.name: self.list_columns_classified_as(t.columns, ColumnType.Category)
            for t in self.dataset_tables.values()
        }

    @computed_field
    @property
    def _DatasetColumnsDateTime(self) -> dict[str, list[str]]:
        """Dictionary of table names and their date-time columns."""
        return {
            t.name: self.list_columns_classified_as(t.columns, ColumnType.DateTime)
            for t in self.dataset_tables.values()
        }

    @computed_field
    @property
    def _DatasetColumnsFact(self) -> dict[str, list[str]]:
        """Dictionary of table names and their fact columns."""
        return {
            t.name: self.list_columns_classified_as(t.columns, ColumnType.Fact)
            for t in self.dataset_tables.values()
        }

    @computed_field
    @property
    def _DatasetColumnsOther(self) -> dict[str, list[str]]:
        """Dictionary of table names and their other columns."""
        return {
            t.name: self.list_columns_classified_as(t.columns, ColumnType.Other)
            for t in self.dataset_tables.values()
        }

    def list_columns_classified_as(
        self,
        columns: dict[str, DatasetTableColumn],
        column_type: ColumnType,
    ) -> list[str]:
        """List the names of columns classified as a given type."""
        return [c.name for c in columns.values() if c.column_type == column_type]

    def is_column_classified_as(
        self,
        column_name: str,
        column_type: ColumnType,
    ) -> bool:
        """Check if a column is classified as a given type."""
        try:
            column_names = getattr(self, f"_DatasetColumns{column_type}")
        except KeyError as ex:
            raise ValueError(f"InvalidColumnType {column_type}") from ex

        return column_name in column_names


""" 

Each Application will expose one endpoint for fetching data and another endpoint for fetching filter options.

Each Application will depend on one Database.

Each Database will have one or more Tables.

Therefore each Application will have one or more Tables.

Each Table will have one or more Columns.

Each Column will have one Data Type, and each Column will be classified as Category, DateTime, Fact or Other.
"""
# class QueryRequestFilter(PydanticBaseModel):
#     """A filter for a query request."""

#     ColumnName: str
#     Operator: Literal[
#         "eq",
#         "neq",
#         "gt",
#         "gte",
#         "lt",
#         "lte",
#         "in",
#         "not_in",
#         "like",
#         "not_like",
#         "is_null",
#         "is_not_null",
#     ]
#     Value: Any


class QueryRequestFilterCategory(PydanticBaseModel):
    """The filter model for category columns."""

    column_name: str
    values: list[str]


class QueryRequestFilterFact(PydanticBaseModel):
    """The filter model for category columns."""

    column_name: str
    values: list[float]


class QueryRequestSelect(PydanticBaseModel):
    """The select model for a query request."""

    kind: Literal["QueryRequestSelect"] = "QueryRequestSelect"
    column_name: str
    alias: str | None = None


AggregationFunction = Literal["COUNT", "SUM", "AVG", "MEDIAN", "MIN", "MAX"]


class QueryRequestAggregation(PydanticBaseModel):
    """The aggregation model for a query request."""

    kind: Literal["QueryRequestAggregation"] = "QueryRequestAggregation"
    column_name: str
    aggregation_function: AggregationFunction
    alias: str


class QueryRequestCustomAggregation(PydanticBaseModel):
    """The aggregation model for a query request using a custom aggregation function."""

    kind: Literal["QueryRequestCustomAggregation"] = "QueryRequestCustomAggregation"
    aggregation_function: str
    alias: str


OrderByDirection = Literal["ASC", "DESC"]


class QueryRequestOrderBy(PydanticBaseModel):
    """The sorting model for a query request."""

    kind: Literal["QueryRequestOrderBy"] = "QueryRequestOrderBy"
    column_name: str
    direction: OrderByDirection


class QueryRequestPagination(PydanticBaseModel):
    """The pagination model for a query request."""

    kind: Literal["QueryRequestPagination"] = "QueryRequestPagination"
    limit: int
    offset: int | None = 0


class QueryRequest(PydanticBaseModel):
    """A request to query an application."""

    kind: Literal["QueryRequest"] = "QueryRequest"
    dataset: Dataset | None = None
    table_name: str

    filters: list[QueryRequestFilterCategory | QueryRequestFilterFact] = []
    select: list[str | tuple[str, str] | QueryRequestSelect] = []
    aggregations: list[
        tuple[str, AggregationFunction, str]
        | QueryRequestAggregation
        | tuple[str, str]
        | QueryRequestCustomAggregation
    ] = []
    order_by: list[tuple[str, OrderByDirection] | QueryRequestOrderBy] = [("1", "ASC")]
    pagination: tuple[int, int] | QueryRequestPagination = (0, 100)

    breakdown: str | None = None

    @computed_field
    @property
    def group_by(self) -> list[int]:
        """The group by for the query request.

        Group by is a virtual property calculated from 'select' and 'breakdown'.
        """
        groups = 0 if self.breakdown is None else 1 + len(self.select)
        return list(range(1, groups + 1))


class MinMaxFilterOption(BaseModel):
    """Filter options from a column classified as Fact.

    Fact columns data types are always numeric.
    The filter options will be the minimum and maximum values of the column.
    """

    kind: Literal["MinMaxFilterOption"]
    Values: tuple[float, float]


class CategoryFilterOption(BaseModel):
    """Filter options from a column classified as Category.

    Category columns data types are always strings.
    The filter options will be the unique values of the column.
    """

    kind: Literal["CategoryFilterOption"]
    Values: list[str]
    ParentId: str | None = None
