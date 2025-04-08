"""Dependencies for the AnySet API."""

from logging import getLogger
import re

from fastapi import HTTPException, Request, status
import orjson
from pydantic import ValidationError

from .models import QueryRequest, RepositoryOption
from .postgres_adapter import PostgresAdapter
from .repository_interface import IRepository
from .settings import settings

logger = getLogger(__name__)


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


def init_repositories():
    """Initialize repositories for each dataset."""
    for d in settings.application_definitions.values():
        if d.adapter == RepositoryOption.PostgreSQL:
            PostgresAdapter(dataset=d)
        else:
            detail = f"UnsupportedRepositoryAdapter {d.adapter}"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


async def get_repository(request: Request) -> IRepository:
    """Resolve and return the repository implementation based on dataset configuration.

    Args:
        request: Request - The FastAPI request object

    Returns:
        IRepository - The repository implementation configured for the dataset

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

    if dataset.adapter == RepositoryOption.PostgreSQL:
        return PostgresAdapter(dataset=dataset)
    else:
        detail = f"UnsupportedRepositoryAdapter {dataset.adapter}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
