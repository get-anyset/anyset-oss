"""Singleton metaclass module."""

from typing import Any, ClassVar


class SingletonMeta(type):
    """Singleton metaclass."""

    _instances: ClassVar[dict[tuple[type, str], Any]] = {}

    def __call__(cls, *args, **kwargs):
        """Create a new instance of the class if it hasn't been created yet.

        It accepts an optional instance_key argument to differentiate between
        instances of the same class.
        """
        instance_key = (cls, kwargs.pop("instance_key", ""))

        if instance_key not in cls._instances:
            cls._instances[instance_key] = super().__call__(*args, **kwargs)

        return cls._instances[instance_key]
