"""FastAPI backend service for the microfrontend application."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from anyset.api import router as anyset_router
from anyset.dependencies import init_repositories
from anyset.settings import Settings, settings

logging.basicConfig(level=settings.log_level)


def create_app(settings: Settings) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Application settings

    Returns:
        Configured FastAPI application
    """
    init_repositories()

    app = FastAPI(
        # title=settings.title,
        # description=settings.description,
        # version=settings.version,
        # debug=settings.debug,
    )

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


app.include_router(anyset_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
