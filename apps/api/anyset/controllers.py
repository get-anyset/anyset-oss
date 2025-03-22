"""Controllers for the AnySet API."""

from typing import Any

from fastapi import APIRouter, HTTPException

from .models import QueryRequest
from .settings import settings

router = APIRouter(prefix="/api")


@router.post("/{path_prefix}/v{version}/query")
def execute_query(path_prefix: str, version: int, query: QueryRequest) -> Any:
    """Execute a query on a dataset."""
    try:
        return settings.application_definitions[f"{path_prefix}/v{version}"]
    except KeyError as ex:
        raise HTTPException(status_code=404, detail=f"ApplicationNotFound {ex}") from ex
