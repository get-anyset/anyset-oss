"""Interface definitions for the AnySet API based on ports and adapters architecture."""

from abc import ABC, abstractmethod

from .models import FilterOptions, QueryRequest, Resultset


class IRepository(ABC):
    """Abstract base class defining the repository interface.

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
