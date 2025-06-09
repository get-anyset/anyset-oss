"""FastAPI router for AnySet."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

from .dependencies import get_repository, inject_dataset
from .models import (
    BaseQueryRequest,
    BaseResultSet,
    CategoricalFilterOption,
    MinMaxFilterOption,
    QueryRequest,
)
from .repository_interface import IRepository

router = APIRouter(prefix="/api")


class QueryRequestDTO(BaseQueryRequest):
    """The DTO for querying a Dataset."""

    pass


class QueryResponseDTO(BaseResultSet):
    """The DTO for query results."""

    pass


@router.post(
    "/{path_prefix}/v{version}/query",
    response_class=ORJSONResponse,
    response_model=QueryResponseDTO,
    response_model_exclude_none=True,
)
async def execute_query(
    path_prefix: str,
    version: int,
    body: QueryRequestDTO,
    query: Annotated[QueryRequest, Depends(inject_dataset)],
    repository: Annotated[IRepository, Depends(get_repository)],
) -> QueryResponseDTO:
    """Execute query on a dataset.

    Args:
        path_prefix: str - The dataset path prefix
        version: str - The dataset version
        body: Request - The FastAPI request object
        query: QueryRequest - The query request (injected from request body)
        repository: RepositoryPort - The repository implementation; Resolved from dataset config

    Returns:
        QueryResponseDTO
    """
    results = await repository.execute_query(query)

    return QueryResponseDTO(**results.model_dump())


FilterOptionsDTO = list[MinMaxFilterOption | CategoricalFilterOption]


@router.get(
    "/{path_prefix}/v{version}/filter-options",
    response_class=ORJSONResponse,
    response_model=FilterOptionsDTO,
    response_model_exclude_none=True,
)
async def get_filter_options(
    path_prefix: str,
    version: int,
    repository: Annotated[IRepository, Depends(get_repository)],
) -> FilterOptionsDTO:
    """Get the filter options for a dataset to populate filter components in the UI.

    Args:
        request: The FastAPI request object
        path_prefix: The dataset path prefix
        version: The dataset version
        repository: The repository implementation (resolved from dataset config)

    Returns:
        Available filter options for the dataset
    """
    return await repository.get_filter_options()
