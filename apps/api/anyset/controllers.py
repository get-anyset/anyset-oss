"""Controllers for the AnySet API."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from .dependencies import inject_dataset
from .models import QueryRequest

router = APIRouter(prefix="/api")


@router.post("/{path_prefix}/v{version}/query")
async def execute_query(
    path_prefix: str,
    version: int,
    query: Annotated[QueryRequest, Depends(inject_dataset)],
) -> Any:
    """Execute a query on a dataset."""
    print(path_prefix, version)
    print(query)
    return "ok"
