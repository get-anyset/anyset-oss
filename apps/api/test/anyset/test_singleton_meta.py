"""Test module for singleton metaclass."""

import pytest

from anyset.singleton_meta import SingletonMeta


def test_singleton_returns_same_instance():
    """Test that multiple instantiations return the same instance."""

    class TestSingleton(metaclass=SingletonMeta):
        """Test class using SingletonMeta."""

        def __init__(self, value=None):
            self.value = value

    instance1 = TestSingleton()
    instance2 = TestSingleton()

    assert instance1 is instance2
    TestSingleton._instances = {}


def test_singleton_with_args():
    """Test that singleton works with initialization arguments."""

    class TestSingleton(metaclass=SingletonMeta):
        """Test class using SingletonMeta."""

        def __init__(self, value=None):
            self.value = value

    instance1 = TestSingleton(value=1)
    instance2 = TestSingleton(value=2)

    assert instance1 is instance2
    assert instance1.value == 1  # Should keep the first initialization value


@pytest.mark.parametrize("instance_key", ["key1", "key2"])
def test_singleton_with_different_keys(instance_key):
    """Test that different instance keys create different instances."""

    class TestSingleton(metaclass=SingletonMeta):
        """Test class using SingletonMeta."""

        def __init__(self, value=None):
            self.value = value

    instance1 = TestSingleton(instance_key=instance_key)
    instance2 = TestSingleton(instance_key=instance_key)

    # Same key should return same instance
    assert instance1 is instance2


def test_multiple_instance_keys():
    """Test that different instance keys create different instances."""

    class TestSingleton(metaclass=SingletonMeta):
        """Test class using SingletonMeta."""

        def __init__(self, value=None):
            self.value = value

    instance1 = TestSingleton(instance_key="key1")
    instance2 = TestSingleton(instance_key="key2")

    # Different keys should return different instances
    assert instance1 is not instance2


def test_singleton_state_persistence():
    """Test that singleton instance maintains its state."""

    class TestSingleton(metaclass=SingletonMeta):
        """Test class using SingletonMeta."""

        def __init__(self, value=None):
            self.value = value

    instance1 = TestSingleton()
    instance1.value = 42

    instance2 = TestSingleton()
    assert instance2.value == 42


def test_different_singleton_classes():
    """Test that different classes using SingletonMeta have separate instances."""

    class TestSingleton(metaclass=SingletonMeta):
        """Test class using SingletonMeta."""

        def __init__(self, value=None):
            self.value = value

    class AnotherTestSingleton(metaclass=SingletonMeta):
        """Another test class using SingletonMeta."""

        pass

    instance1 = TestSingleton()
    instance2 = AnotherTestSingleton()

    assert instance1 is not instance2
