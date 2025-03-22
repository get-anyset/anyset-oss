"""Application settings configuration using Pydantic."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API application settings.

    All settings can be overridden with environment variables using the prefix APP_
    For example: APP_PORT=8080
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = Field(default=True, description="Enable debug mode")

    cors_allow_credentials: bool = True
    cors_allow_headers: list[str] = ["*"]
    cors_allow_methods: list[str] = ["*"]
    cors_origins: list[str] = ["*"]


settings = Settings()


def get_settings() -> Settings:
    """Return the settings instance.

    Can be used as a FastAPI dependency to access settings.

    Returns:
        Settings: Application settings
    """
    return settings
