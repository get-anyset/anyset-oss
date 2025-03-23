"""Models for the AnySet Framework."""

from datetime import datetime
from enum import Enum
from typing import Generic, Literal, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel as PydanticBaseModel
from pydantic import computed_field, model_validator
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
    custom_aggregation_functions: dict[str, str] | None = None

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
        table_name: str,
    ) -> bool:
        """Check if a column is classified as a given type."""
        try:
            column_names = getattr(self, f"_DatasetColumns{column_type.value}")[table_name]
        except KeyError as ex:
            raise ValueError(f"InvalidColumnType {column_type}") from ex

        return column_name in column_names


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


class QueryRequest(PydanticBaseModel):
    """A request to query a dataset."""

    kind: Literal["QueryRequest"] = "QueryRequest"
    dataset: Dataset
    table_name: str

    filters: list[QueryRequestFilterCategory | QueryRequestFilterFact] = []
    select: list[QueryRequestSelect] = []
    aggregations: list[QueryRequestAggregation | QueryRequestCustomAggregation] = []
    order_by: list[QueryRequestOrderBy] = [QueryRequestOrderBy(column_name="1", direction="ASC")]
    pagination: QueryRequestPagination = QueryRequestPagination(limit=100, offset=0)

    breakdown: str | None = None


class QueryRequestDTO(PydanticBaseModel):
    """A request to query a dataset."""

    kind: Literal["QueryRequestDTO"] = "QueryRequestDTO"
    dataset: Dataset
    table_name: str

    filters: list[QueryRequestFilterCategory | QueryRequestFilterFact] = []
    select: list[str | tuple[str, str] | QueryRequestSelect] = []
    aggregations: list[
        tuple[str, AggregationFunction, str]
        | QueryRequestAggregation
        | tuple[str, str]
        | QueryRequestCustomAggregation
    ] = []
    order_by: list[tuple[str, OrderByDirection] | QueryRequestOrderBy] = [
        QueryRequestOrderBy(column_name="1", direction="ASC")
    ]
    pagination: tuple[int, int] | QueryRequestPagination = QueryRequestPagination(
        limit=100, offset=0
    )

    breakdown: str | None = None

    @computed_field
    @property
    def group_by(self) -> list[int]:
        """The group by for the query request.

        Group by is a virtual property calculated from 'select' and 'breakdown'.
        """
        groups = 0 if self.breakdown is None else 1 + len(self.select)
        return list(range(1, groups + 1))

    @model_validator(mode="after")
    def validate_table_name(self) -> "QueryRequestDTO":
        """Validate the table_name exists in the dataset."""
        if self.table_name not in [t.name for t in self.dataset.dataset_tables.values()]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"TableNotFound {self.dataset._id}:{self.table_name}",
            )
        return self

    @model_validator(mode="after")
    def validate_filters(self) -> "QueryRequestDTO":
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
    def validate_select(self) -> "QueryRequestDTO":
        """Validate the select columns exist in the table."""
        normalized_select: list[QueryRequestSelect] = []
        for select in self.select:
            if isinstance(select, str):
                s = QueryRequestSelect(column_name=select, alias=select)
            elif isinstance(select, tuple):
                s = QueryRequestSelect(column_name=select[0], alias=select[1])
            else:
                s = select

            if s.column_name not in [
                c.name for c in self.dataset.dataset_tables[self.table_name].columns.values()
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SelectColumnNotFound {s.column_name}",
                )

            normalized_select.append(s)

        self.select = normalized_select  # type: ignore
        return self

    @model_validator(mode="after")
    def validate_aggregations(self) -> "QueryRequestDTO":
        """Validate the aggregations."""
        normalized_aggregations: list[QueryRequestAggregation | QueryRequestCustomAggregation] = []
        for aggregation in self.aggregations:
            agg: QueryRequestAggregation | QueryRequestCustomAggregation

            if isinstance(aggregation, tuple) and len(aggregation) == 3:
                agg = QueryRequestAggregation(
                    column_name=aggregation[0],
                    aggregation_function=aggregation[1],
                    alias=aggregation[2],
                )
            elif isinstance(aggregation, tuple) and len(aggregation) == 2:
                agg = QueryRequestCustomAggregation(
                    aggregation_function=aggregation[0],
                    alias=aggregation[1],
                )
            elif not isinstance(aggregation, tuple):
                agg = aggregation

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

            normalized_aggregations.append(agg)

        self.aggregations = normalized_aggregations  # type: ignore
        return self

    @model_validator(mode="after")
    def validate_order_by(self) -> "QueryRequestDTO":
        """Validate sorting columns exist in the table."""
        normalized_order_by: list[QueryRequestOrderBy] = []
        for order_by in self.order_by:
            if isinstance(order_by, tuple):
                normalized_order_by.append(
                    QueryRequestOrderBy(column_name=order_by[0], direction=order_by[1])
                )
            else:
                normalized_order_by.append(order_by)

        self.order_by = normalized_order_by  # type: ignore
        return self

    @model_validator(mode="after")
    def validate_pagination(self) -> "QueryRequestDTO":
        """Validate the pagination."""
        if isinstance(self.pagination, tuple) and (
            self.pagination[0] < 0 or self.pagination[1] <= 0
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"InvalidPaginationParameters skip={self.pagination[0]} limit={self.pagination[1]}",  # noqa: E501
            )

        if isinstance(self.pagination, tuple):
            self.pagination = QueryRequestPagination(
                offset=self.pagination[0],
                limit=self.pagination[1],
            )
        return self


class QueryResponseColumn(PydanticBaseModel):
    """A column in a query response."""

    kind: Literal["QueryResponseColumn"] = "QueryResponseColumn"
    alias: str
    breakdown: str | None = None
    data: list[str | None] | list[float | None] | list[bool | None] | list[datetime | None]


class QueryResponseDTO(PydanticBaseModel):
    """A response to a query request."""

    kind: Literal["QueryResponse"] = "QueryResponse"
    dataset: str
    version: int
    rows: int
    columns: list[QueryResponseColumn]


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


FilterOptionsDTO = list[FilterOptionMinMax | FilterOptionCategory]
