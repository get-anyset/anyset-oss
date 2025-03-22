"""FastAPI backend service for the microfrontend application."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from anyset.settings import Settings, settings


def create_app(settings: Settings) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Application settings

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        # title=settings.title,
        # description=settings.description,
        # version=settings.version,
        # debug=settings.debug,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    return app


app = create_app(settings)


@app.get("/")
async def root() -> dict[str, str]:
    """Return a welcome message.

    Returns:
        dict: A welcome message dictionary
    """
    return {"message": "Welcome to the Microfrontend API"}


@app.get("/api/items")
async def get_items() -> list[dict]:
    """Get a list of items.

    Returns:
        list: A list of items with their details
    """
    return [
        {"id": 1, "name": "Item 1", "description": "Description for Item 1"},
        {"id": 2, "name": "Item 2", "description": "Description for Item 2"},
        {"id": 3, "name": "Item 3", "description": "Description for Item 3"},
    ]


# Example of using settings as a dependency in a route
@app.get("/api/info")
async def get_info() -> dict[str, str]:
    """Get API information.

    Args:
        settings: Application settings from dependency injection

    Returns:
        dict: API information
    """
    return {
        "title": "settings.title",
        "version": "settings.version",
        "description": "settings.description",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
