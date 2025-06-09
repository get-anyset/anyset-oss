"""Application settings configuration using Pydantic."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
import tomli

from .models import Dataset

load_dotenv()


class Settings(BaseSettings):
    """API application settings.

    All settings can be overridden with environment variables using the prefix APP_
    For example: APP_PORT=8080
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False

    cors_allow_credentials: bool = True
    cors_allow_headers: list[str] = ["*"]
    cors_allow_methods: list[str] = ["*"]
    cors_origins: list[str] = ["*"]

    application_definitions_dir: str = "../../app-definitions"

    @computed_field
    @property
    def application_definitions(self) -> dict[str, Dataset]:
        """A map of application definitions.

        The keys are the compound path of Dataset.path_prefix and Dataset.version, e.g. "sample/v1".
        """
        definitions = {}
        app_path = Path(self.application_definitions_dir).resolve()

        for toml_file in app_path.rglob("*.toml"):
            with open(toml_file, "rb") as f:
                data = tomli.load(f)
                dataset = Dataset.model_validate(data)
                key = f"{dataset.path_prefix}/v{dataset.version}"
                definitions[key] = dataset

        return definitions


settings = Settings()


def get_settings() -> Settings:
    """Return the settings instance.

    Can be used as a FastAPI dependency to access settings.

    Returns:
        Settings: Application settings
    """
    return settings
