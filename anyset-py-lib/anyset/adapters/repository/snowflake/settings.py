"""Snowflake adapter settings."""

from functools import cached_property
import logging
from typing import Literal

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


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
    authenticator: Literal["snowflake", "snowflake_jwt"] = "snowflake"

    schema_: str = Field(alias="schema", default="")

    database: str = ""
    warehouse: str = ""
    role: str = ""
    user: str = ""

    # password-based authentication
    password: str | None = None

    # pk-based authentication
    private_key_str: str | None = None
    private_key_passphrase: str | None = None

    pool_size: int = 5
    pool_max_overflow: int = 10
    query_timeout: int = 30

    @computed_field  # type: ignore
    @cached_property
    def private_key(self) -> bytes | None:
        """Return snowflake private key as bytes.

        Returns:
            bytes: returns snowflake private key as bytes.

        """
        if self.private_key_str is None or self.private_key_passphrase is None:
            return None

        try:
            private_key_bytes = self.private_key_str.replace("\\n", "\n").encode()
            serialized_private_key = serialization.load_pem_private_key(
                private_key_bytes,
                password=self.private_key_passphrase.encode(),
                backend=default_backend(),
            )

            return serialized_private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        except (ValueError, TypeError, InvalidKey) as ex:
            raise RuntimeError(f"SnowflakePrivateKeySerializationFailed {ex}") from ex


snowflake_settings = SnowflakeSettings()


def get_snowflake_settings() -> SnowflakeSettings:
    """Return the settings instance.

    Can be used as a FastAPI dependency to access Snowflake settings.

    Returns:
        SnowflakeSettings: Snowflake connection settings
    """
    return snowflake_settings
