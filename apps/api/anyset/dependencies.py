"""Dependencies for the AnySet API."""

import orjson
from fastapi import HTTPException, Request, status

from .models import QueryRequest
from .settings import settings


async def inject_dataset(request: Request) -> QueryRequest:
    """Inject dataset definition into the request.

    Args:
        request: The FastAPI request object

    Returns:
        QueryRequest

    Raises:
        HTTPException: When dataset definition not found
    """
    path = request.url.path.removesuffix("/").removesuffix("/query").removeprefix("/api/")

    if path not in settings.application_definitions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"DatasetDefinitionNotFound {path}"
        )

    dataset = settings.application_definitions[path]

    body_bytes = await request.body()

    if body_bytes:
        body_json = orjson.loads(body_bytes)
    else:
        body_json = {}

    return QueryRequest(**body_json, dataset=dataset)
