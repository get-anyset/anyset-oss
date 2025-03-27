"""Dependencies for the AnySet API."""

import re

from fastapi import HTTPException, Request, status
import orjson
from pydantic import ValidationError

from .models import RepositoryAdapter
from .postgres_adapter import PostgresRepository
from .repository import QueryRequest, RepositoryPort
from .settings import settings


def get_dataset(path: str, masks: list[str]):
    """Get dataset definition from path parameters.

    Args:
        path: str - The request path
        masks: list[str] - The masks to replace in the path

    Returns:
        Dataset - The dataset definition

    Raises:
        HTTPException: When dataset definition not found
    """
    for mask in masks:
        dataset_path = re.sub(mask, r"\1", path)
        if dataset_path in settings.application_definitions:
            return settings.application_definitions[dataset_path]

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"DatasetDefinitionNotFound {path}",
    )


async def inject_dataset(request: Request) -> QueryRequest:
    """Inject dataset definition into the request.

    Args:
        request: Request - The FastAPI request object

    Returns:
        QueryRequest

    Raises:
        HTTPException: When dataset definition not found
    """
    dataset = get_dataset(
        request.url.path,
        [
            r"\/api\/([a-zA-Z0-9_-]+\/v\d+)\/query",
        ],
    )

    body_bytes = await request.body()

    if body_bytes:
        body_json = orjson.loads(body_bytes)
    else:
        body_json = {}

    try:
        return QueryRequest(**body_json, dataset=dataset)
    except ValidationError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ex.errors()) from ex


async def get_repository(request: Request) -> RepositoryPort:
    """Resolve and return the repository implementation based on dataset configuration.

    Args:
        request: Request - The FastAPI request object

    Returns:
        RepositoryPort - The repository implementation configured for the dataset

    Raises:
        HTTPException - When dataset definition not found or adapter not supported
    """
    dataset = get_dataset(
        request.url.path,
        [
            r"\/api\/([a-zA-Z0-9_-]+\/v\d+)\/filter-options",
            r"\/api\/([a-zA-Z0-9_-]+\/v\d+)\/query",
        ],
    )

    if dataset.adapter == RepositoryAdapter.PostgreSQL:
        return PostgresRepository(dataset=dataset)
    else:
        detail = f"UnsupportedRepositoryAdapter {dataset.adapter}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
