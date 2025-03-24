"""Port definitions for the AnySet API based on ports and adapters architecture."""

from abc import ABC, abstractmethod
from typing import Literal

from fastapi import HTTPException, status
from pydantic import model_validator

from .models import (
    BaseQueryRequest,
    BaseResultset,
    ColumnType,
    Dataset,
    FilterOptionCategory,
    FilterOptionMinMax,
)


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
        if self.pagination.offset < 0 or self.pagination.limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"InvalidPaginationParameters offset={self.pagination.offset} limit={self.pagination.limit}",  # noqa: E501
            )
        return self


class Resultset(BaseResultset):
    """A resultset from a query."""

    kind: Literal["Resultset"] = "Resultset"


FilterOptions = list[FilterOptionMinMax | FilterOptionCategory]


class RepositoryPort(ABC):
    """Abstract base class defining the repository port interface.

    This port is used to execute queries and retrieve filter options.
    Adapters implementing this port will handle the actual data retrieval logic.
    """

    @abstractmethod
    async def execute_query(self, query: QueryRequest) -> Resultset:
        """Execute a query on a dataset.

        Args:
            query: QueryRequest - The query request

        Returns:
            QueryResponse - The query response
        """
        raise NotImplementedError("MethodNotImplementedBySubClass execute_query")

    @abstractmethod
    async def get_filter_options(self) -> FilterOptions:
        """Get filter options for building query filters.

        Returns:
            FilterOptions - Available filter options
        """
        raise NotImplementedError("MethodNotImplementedBySubClass get_filter_options")
