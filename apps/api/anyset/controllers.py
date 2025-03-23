"""Controllers for the AnySet API."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

from .dependencies import inject_dataset
from .models import (
    FilterOptionsDTO,
    QueryRequestDTO,
    QueryResponseDTO,
)

router = APIRouter(prefix="/api")


@router.post(
    "/{path_prefix}/v{version}/query",
    response_class=ORJSONResponse,
    response_model=QueryResponseDTO,
    response_model_exclude_none=True,
)
async def execute_query(
    path_prefix: str,
    version: int,
    query: Annotated[QueryRequestDTO, Depends(inject_dataset)],
) -> QueryResponseDTO:
    """Execute a query on a dataset."""
    print(path_prefix, version)
    print(query)
    return QueryResponseDTO(
        dataset=query.dataset._id,
        version=query.dataset.version,
        rows=0,
        columns=[],
    )


@router.get(
    "/{path_prefix}/v{version}/filter-options",
    response_class=ORJSONResponse,
    response_model=FilterOptionsDTO,
    response_model_exclude_none=True,
)
async def get_filter_options(path_prefix: str, version: int) -> FilterOptionsDTO:
    """Get the filter options for a dataset to populate filter components in the UI."""
    return []
