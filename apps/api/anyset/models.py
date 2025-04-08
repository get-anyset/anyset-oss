"""Models for the AnySet Framework."""

from datetime import datetime
from enum import Enum
from typing import Generic, Literal, TypeVar

from fastapi import HTTPException, status
from pydantic import (
    BaseModel as PydanticBaseModel,
    computed_field,
    model_validator,
)
from slugify import slugify


class BaseModel(PydanticBaseModel):
    """Base properties for all models."""

    kind: str
    name: str
    description: str | None = None

    @computed_field  # type: ignore
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
    parent: str | None = None


class DatasetTable(BaseModel):
    """A table in a dataset."""

    kind: Literal["DatasetTable"] = "DatasetTable"
    columns: dict[str, DatasetTableColumn]


class RepositoryOption(str, Enum):
    """The repository adapter options."""

    InMemory = "InMemory"
    PostgreSQL = "PostgreSQL"
    Snowflake = "Snowflake"
    Custom = "Custom"


class Dataset(BaseModel):
    """A dataset is a collection of data tables."""

    kind: Literal["Dataset"] = "Dataset"
    path_prefix: str
    version: int

    adapter: RepositoryOption
    adapter_config: dict[str, str | int | float | bool] = {}
    # custom_adapter_path: str | None = None # TODO: Add this functionality

    dataset_tables: dict[str, DatasetTable]

    custom_aggregation_functions: dict[str, str] | None = None

    @computed_field  # type: ignore
    @property
    def dataset_columns_category(self) -> dict[str, list[str]]:
        """Dictionary of table names and their category columns."""
        return {
            t.name: self.list_columns_classified_as(t.columns, ColumnType.Category)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_columns_datetime(self) -> dict[str, list[str]]:
        """Dictionary of table names and their date-time columns."""
        return {
            t.name: self.list_columns_classified_as(t.columns, ColumnType.DateTime)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_columns_fact(self) -> dict[str, list[str]]:
        """Dictionary of table names and their fact columns."""
        return {
            t.name: self.list_columns_classified_as(t.columns, ColumnType.Fact)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_columns_other(self) -> dict[str, list[str]]:
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
        table_name: str,
    ) -> bool:
        """Check if a column is classified as a given type."""
        try:
            attr_name = f"dataset_columns_{column_type.value.lower()}"
            column_names = getattr(self, attr_name)[table_name]
            return column_name in column_names
        except (KeyError, AttributeError) as ex:
            raise ValueError(f"InvalidColumnType {column_type}") from ex


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

    kind: Literal["QueryRequestFilterCategory"] = "QueryRequestFilterCategory"
    column_name: str
    values: list[str]


class QueryRequestFilterFact(PydanticBaseModel):
    """The filter model for category columns."""

    kind: Literal["QueryRequestFilterFact"] = "QueryRequestFilterFact"
    column_name: str
    values: tuple[float | None, float] | tuple[float, float | None]


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


class BaseQueryRequest(PydanticBaseModel):
    """Base for a query extended by QueryRequestDTO and (repository) Query."""

    table_name: str

    filters: list[QueryRequestFilterCategory | QueryRequestFilterFact] = []
    select: list[QueryRequestSelect] = []
    aggregations: list[QueryRequestAggregation | QueryRequestCustomAggregation] = []
    order_by: list[QueryRequestOrderBy] = []
    pagination: QueryRequestPagination = QueryRequestPagination(limit=100, offset=0)

    breakdown: str | None = None

    @computed_field  # type: ignore
    @property
    def group_by(self) -> list[str]:
        """The group by for the query request.

        Group by is a virtual property calculated from 'select' and 'breakdown'.
        """
        group_by_columns = set()

        for s in self.select:
            group_by_columns.add(s.alias or s.column_name)
        for o in self.order_by:
            group_by_columns.add(o.column_name)
        if self.breakdown is not None:
            group_by_columns.add(self.breakdown)

        return list(group_by_columns)


class BaseResultsetColumn(PydanticBaseModel):
    """A column in a query response."""

    kind: Literal["BaseResultsetColumn"] = "BaseResultsetColumn"
    alias: str
    breakdown: str | None = None
    data: list[str | None] | list[float | None] | list[bool | None] | list[datetime | None]


class BaseResultset(PydanticBaseModel):
    """Base for a resultset extended by QueryResponseDTO and (repository) Resultset."""

    dataset: str
    version: int
    rows: int
    columns: list[BaseResultsetColumn]


class QueryRequest(BaseQueryRequest):
    """A request to query a dataset."""

    kind: Literal["QueryRequest"] = "QueryRequest"
    dataset: Dataset

    @model_validator(mode="after")
    def validate_table_name(self) -> "QueryRequest":
        """Validate the table_name exists in the dataset."""
        if self.table_name not in [t.name for t in self.dataset.dataset_tables.values()]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"TableNotFound {self.dataset._id}:{self.table_name}",
            )
        return self

    @model_validator(mode="after")
    def validate_filters(self) -> "QueryRequest":
        """Validate the filter columns exist in the table and values match the column data type."""
        for filter in self.filters:
            is_category = self.dataset.is_column_classified_as(
                filter.column_name,
                ColumnType.Category,
                self.table_name,
            )
            if filter.kind == "QueryRequestFilterCategory" and not is_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"QueryRequestFilterCategoryInvalidColumn {filter.column_name}",
                )
            is_fact = self.dataset.is_column_classified_as(
                filter.column_name,
                ColumnType.Fact,
                self.table_name,
            )
            if filter.kind == "QueryRequestFilterFact" and not is_fact:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"QueryRequestFilterFactInvalidColumn {filter.column_name}",
                )
        return self

    @model_validator(mode="after")
    def validate_select(self) -> "QueryRequest":
        """Validate the select columns exist in the table."""
        for select in self.select:
            if select.column_name not in [
                c.name for c in self.dataset.dataset_tables[self.table_name].columns.values()
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SelectColumnNotFound {select.column_name}",
                )

        return self

    @model_validator(mode="after")
    def validate_aggregations(self) -> "QueryRequest":
        """Validate the aggregations."""
        for agg in self.aggregations:
            if agg.kind == "QueryRequestCustomAggregation" and (
                self.dataset.custom_aggregation_functions is None
                or agg.aggregation_function not in self.dataset.custom_aggregation_functions
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"CustomAggregationFunctionNotFound {agg.aggregation_function}",
                )

            if agg.kind == "QueryRequestAggregation" and not self.dataset.is_column_classified_as(
                column_name=agg.column_name,
                column_type=ColumnType.Fact,
                table_name=self.table_name,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"AggregationColumnNotFound {agg.column_name}",
                )

        return self

    @model_validator(mode="after")
    def validate_order_by(self) -> "QueryRequest":
        """Validate sorting columns exist in the table."""
        return self

    @model_validator(mode="after")
    def validate_pagination(self) -> "QueryRequest":
        """Validate the pagination."""
        if self.pagination.offset is not None and (
            self.pagination.offset < 0 or self.pagination.limit <= 0
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"InvalidPaginationParameters offset={self.pagination.offset} limit={self.pagination.limit}",  # noqa: E501
            )
        return self


class Resultset(BaseResultset):
    """A resultset from a query."""

    kind: Literal["Resultset"] = "Resultset"


T = TypeVar("T")


class FilterOptionValue(PydanticBaseModel, Generic[T]):
    """A filter option."""

    label: str
    value: T


class FilterOptionMinMax(BaseModel):
    """Filter options from a column classified as Fact.

    Fact columns data types are always numeric.
    The filter options will be the minimum and maximum values of the column.
    """

    kind: Literal["FilterOptionMinMax"] = "FilterOptionMinMax"
    values: tuple[FilterOptionValue[float], FilterOptionValue[float]]


class FilterOptionCategory(BaseModel):
    """Filter options from a column classified as Category.

    Category columns data types are always strings.
    The filter options will be the unique values of the column.
    """

    kind: Literal["FilterOptionCategory"] = "FilterOptionCategory"
    values: list[FilterOptionValue[str]]
    parent_id: str | None = None


FilterOptions = list[FilterOptionMinMax | FilterOptionCategory]
