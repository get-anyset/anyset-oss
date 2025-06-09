"""Models for the AnySet Framework."""

from datetime import datetime
from enum import Enum
from typing import Literal

from fastapi import HTTPException, status
from pydantic import (
    BaseModel as PydanticBaseModel,
    computed_field,
    model_validator,
)
from slugify import slugify


class ColumnType(str, Enum):
    """The class of a column."""

    boolean = "boolean"
    datetime = "datetime"
    numeric_fact = "numeric_fact"
    numeric_other = "numeric_other"
    text_category = "text_category"
    text_other = "text_other"


class RepositoryOption(str, Enum):
    """The repository adapter options."""

    in_memory = "in_memory"
    postgresql = "postgresql"
    snowflake = "snowflake"
    custom = "custom"


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


class DatasetTableColumn(BaseModel):
    """A column in a table."""

    kind: Literal["DatasetTableColumn"] = "DatasetTableColumn"
    column_type: ColumnType


class DatasetTable(BaseModel):
    """A table in a dataset."""

    kind: Literal["DatasetTable"] = "DatasetTable"
    columns: dict[str, DatasetTableColumn]


class Dataset(BaseModel):
    """A dataset is a collection of data tables."""

    kind: Literal["Dataset"] = "Dataset"
    path_prefix: str
    version: int

    adapter: RepositoryOption
    adapter_config: dict[str, str | int | float | bool] = {}
    # custom_adapter_path: str | None = None # TODO: Add this functionality

    dataset_tables: dict[str, DatasetTable]

    category_hierarchies: dict[str, list[tuple[str, str]]] = {}

    custom_aggregation_functions: dict[str, str] = {}

    @computed_field  # type: ignore
    @property
    def dataset_cols_boolean(self) -> dict[str, list[str]]:
        """Dictionary of table names and their boolean columns."""
        return {
            t.name: self.list_cols_classified_as(t.columns, ColumnType.boolean)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_cols_datetime(self) -> dict[str, list[str]]:
        """Dictionary of table names and their datetime columns."""
        return {
            t.name: self.list_cols_classified_as(t.columns, ColumnType.datetime)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_cols_numeric_fact(self) -> dict[str, list[str]]:
        """Dictionary of table names and their fact columns."""
        return {
            t.name: self.list_cols_classified_as(t.columns, ColumnType.numeric_fact)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_cols_numeric_other(self) -> dict[str, list[str]]:
        """Dictionary of table names and their other numeric columns."""
        return {
            t.name: self.list_cols_classified_as(t.columns, ColumnType.numeric_other)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_cols_text_category(self) -> dict[str, list[str]]:
        """Dictionary of table names and their category columns."""
        return {
            t.name: self.list_cols_classified_as(t.columns, ColumnType.text_category)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_cols_text_other(self) -> dict[str, list[str]]:
        """Dictionary of table names and their other text columns."""
        return {
            t.name: self.list_cols_classified_as(t.columns, ColumnType.text_other)
            for t in self.dataset_tables.values()
        }

    @computed_field  # type: ignore
    @property
    def dataset_cols_all(self) -> list[tuple[str, str]]:
        """Flat list of table names and their columns."""
        return [(t.name, c.name) for t in self.dataset_tables.values() for c in t.columns.values()]

    @computed_field  # type: ignore
    @property
    def category_hierarchies_cols_all(self) -> list[tuple[str, str]]:
        """Flat list of category hierarchy columns."""
        return [item for hierarchy in self.category_hierarchies.values() for item in hierarchy]

    def list_cols_classified_as(
        self,
        columns: dict[str, DatasetTableColumn],
        column_type: ColumnType,
    ) -> list[str]:
        """List the names of columns classified as a given type."""
        return [c.name for c in columns.values() if c.column_type == column_type]

    def is_col_classified_as(
        self,
        column_name: str,
        column_type: ColumnType,
        table_name: str,
    ) -> bool:
        """Check if a column is classified as a given type."""
        try:
            attr_name = f"dataset_cols_{column_type.value.lower()}"
            column_names = getattr(self, attr_name)[table_name]
            return column_name in column_names
        except (KeyError, AttributeError) as ex:
            raise ValueError(f"InvalidColumnType {column_type}") from ex

    def is_col_in_dataset(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        return (table_name, column_name) in self.dataset_cols_all

    def is_col_in_category_hierarchy(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a category hierarchy."""
        return (table_name, column_name) in self.category_hierarchies_cols_all

    @model_validator(mode="after")
    def validate_dataset_table_column_keys(self) -> "Dataset":
        """Validate dataset table and column keys match their name properties."""
        for table_key, table in self.dataset_tables.items():
            if table_key != table.name:
                raise ValueError(
                    f"DatasetTableKeyMismatch dataset '{self._id}' "
                    f"table_key '{table_key}' table_name '{table.name}'"
                )
            for column_key, column in table.columns.items():
                if column_key != column.name:
                    raise ValueError(
                        f"DatasetTableColumnKeyMismatch dataset '{self._id}' table '{table.name}' "
                        f"column_key '{column_key}' column_name '{column.name}'"
                    )
        return self

    @model_validator(mode="after")
    def validate_category_hierarchy_fields(self) -> "Dataset":
        """Validate category hierarchy fields in the dataset."""
        failed_validations = [
            item
            for item in self.category_hierarchies_cols_all
            if not self.is_col_in_dataset(item[0], item[1])
        ]
        if failed_validations:
            raise ValueError(
                f"CategoryHierarchyFieldNotFound dataset '{self._id}' fields '{failed_validations}'"
            )
        return self


class QueryRequestFilter(PydanticBaseModel):
    """A filter for a query request."""


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


class BaseResultSetColumn(PydanticBaseModel):
    """A column in a query response."""

    kind: Literal["BaseResultSetColumn"] = "BaseResultSetColumn"
    alias: str
    breakdown: str | None = None
    data: list[str | None] | list[float | None] | list[bool | None] | list[datetime | None]


class BaseResultSet(PydanticBaseModel):
    """Base for a result set extended by QueryResponseDTO and (repository) Resultset."""

    dataset: str
    version: int
    rows: int
    columns: list[BaseResultSetColumn]


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
            is_category = self.dataset.is_col_classified_as(
                filter.column_name,
                ColumnType.text_category,
                self.table_name,
            )
            if filter.kind == "QueryRequestFilterCategory" and not is_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"QueryRequestFilterCategoryInvalidColumn {filter.column_name}",
                )
            is_fact = self.dataset.is_col_classified_as(
                filter.column_name,
                ColumnType.numeric_fact,
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

            if agg.kind == "QueryRequestAggregation" and not self.dataset.is_col_classified_as(
                column_name=agg.column_name,
                column_type=ColumnType.numeric_fact,
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


class ResultSet(BaseResultSet):
    """A result set from a query."""

    kind: Literal["ResultSet"] = "ResultSet"


class MinMaxFilterOption(BaseModel):
    """Filter options from a column classified as Fact.

    Fact columns data types are always numeric.
    The filter options will be the minimum and maximum values of the column.
    """

    kind: Literal["MinMaxFilterOption"] = "MinMaxFilterOption"
    values: tuple[datetime, datetime] | tuple[float, float]


class CategoricalFilterOption(BaseModel):
    """Filter options from a column classified as Boolean.

    Boolean category columns data types are always strings.
    The filter options will be the unique values of the column.
    """

    kind: Literal["CategoricalFilterOption"] = "CategoricalFilterOption"
    values: (
        list[bool]
        | list[str]
        | list[tuple[bool, "CategoricalFilterOption"]]
        | list[tuple[str, "CategoricalFilterOption"]]
    )


FilterOptions = list[MinMaxFilterOption | CategoricalFilterOption]
