"""Port definitions for the AnySet API based on ports and adapters architecture."""

from abc import ABC, abstractmethod

from .models import FilterOptionsDTO, QueryRequest, QueryResponseDTO


class RepositoryPort(ABC):
    """Abstract base class defining the repository port interface.

    This port is used to execute queries and retrieve filter options.
    Adapters implementing this port will handle the actual data retrieval logic.
    """

    @abstractmethod
    async def execute_query(self, query: QueryRequest) -> QueryResponseDTO:
        """Execute a query on a dataset.

        Args:
            query: QueryRequest - The query request

        Returns:
            QueryResponse - The query response
        """
        raise NotImplementedError("Method execute_query must be implemented by subclasses")

    @abstractmethod
    async def get_filter_options(self) -> FilterOptionsDTO:
        """Get filter options for building query filters.

        Returns:
            FilterOptions - Available filter options
        """
        raise NotImplementedError("Method get_filter_options must be implemented by subclasses")
