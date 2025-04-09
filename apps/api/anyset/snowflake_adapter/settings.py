"""Snowflake adapter settings."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SnowflakeSettings(BaseSettings):
    """Settings for Snowflake connection.

    All settings can be overridden with environment variables using the prefix SNOWFLAKE_
    For example: SNOWFLAKE_ACCOUNT=xy12345.us-east-1
    """

    model_config = SettingsConfigDict(
        env_prefix="SNOWFLAKE_",
        case_sensitive=False,
        extra="ignore",
    )

    account: str = "localhost"
    authenticator: Literal["snowflake", "snowflake_jwt", "externalbrowser"] = "snowflake"

    schema_: str = Field(alias="schema", default="")

    database: str = ""
    warehouse: str = ""
    role: str = ""
    user: str = ""
    password: str = ""

    pool_size: int = 5
    pool_max_overflow: int = 10
    query_timeout: int = 30


snowflake_settings = SnowflakeSettings()


def get_snowflake_settings() -> SnowflakeSettings:
    """Return the settings instance.

    Can be used as a FastAPI dependency to access Snowflake settings.

    Returns:
        SnowflakeSettings: Snowflake connection settings
    """
    return snowflake_settings
