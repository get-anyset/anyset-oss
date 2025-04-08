"""Singleton metaclass module."""

from logging import getLogger
from typing import Any, ClassVar

from .models import Dataset

logger = getLogger(__name__)


class SingletonMeta(type):
    """Singleton metaclass."""

    _instances: ClassVar[dict[tuple[type, str], Any]] = {}

    def __call__(cls, *args, **kwargs):
        """Create a new instance of the class if it hasn't been created yet.

        It accepts an optional instance_key argument to differentiate between
        instances of the same class.
        """
        dataset = kwargs.get("dataset", None)
        repository_instance_key = (
            f"{dataset.path_prefix}/{dataset.version}" if isinstance(dataset, Dataset) else ""
        )
        logger.debug(f"__call__repository_instance_key '{repository_instance_key}'")
        instance_key = (cls, repository_instance_key)

        if instance_key not in cls._instances:
            logger.debug(f"__call__instance_key '{cls.__name__} {instance_key}' not in _instances")
            cls._instances[instance_key] = super().__call__(*args, **kwargs)
        else:
            logger.debug(f"__call__instance_key '{cls.__name__} {instance_key}' already exists")

        return cls._instances[instance_key]
