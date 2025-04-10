"""PostgreSQL adapter settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    """Settings for PostgreSQL connection.

    All settings can be overridden with environment variables using the prefix PG_
    For example: PG_HOST=localhost
    """

    model_config = SettingsConfigDict(
        env_prefix="PG_",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = ""
    port: int = 5432
    user: str = ""
    password: str = ""
    database: str = ""

    pool_min_size: int = 1
    pool_max_size: int = 10
    query_timeout: int = 30


postgres_settings = PostgresSettings()


def get_postgres_settings() -> PostgresSettings:
    """Return the settings instance.

    Can be used as a FastAPI dependency to access PostgreSQL settings.

    Returns:
        PostgresSettings: PostgreSQL connection settings
    """
    return postgres_settings
