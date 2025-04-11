"""Test module for singleton metaclass."""

from anyset.models import Dataset, RepositoryOption
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
    TestSingleton._instances = {}


def test_singleton_with_dataset():
    """Test that singleton works with dataset parameter."""

    class TestRepository(metaclass=SingletonMeta):
        """Test repository class using SingletonMeta."""

        def __init__(self, dataset=None):
            self.dataset = dataset
            self.initialized = True

    # Create different dataset instances
    dataset1 = Dataset(
        name="test1",
        path_prefix="test/path1",
        version=1,
        adapter=RepositoryOption.in_memory,
        dataset_tables={},
    )

    dataset2 = Dataset(
        name="test2",
        path_prefix="test/path1",  # Same path
        version=1,  # Same version
        adapter=RepositoryOption.in_memory,
        dataset_tables={},
    )

    dataset3 = Dataset(
        name="test3",
        path_prefix="test/path2",  # Different path
        version=1,
        adapter=RepositoryOption.in_memory,
        dataset_tables={},
    )

    dataset4 = Dataset(
        name="test4",
        path_prefix="test/path1",  # Same path
        version=2,  # Different version
        adapter=RepositoryOption.in_memory,
        dataset_tables={},
    )

    # Test same path/version gives same instance
    repo1 = TestRepository(dataset=dataset1)
    repo2 = TestRepository(dataset=dataset2)
    assert repo1 is repo2

    # Test different path gives different instance
    repo3 = TestRepository(dataset=dataset3)
    assert repo1 is not repo3

    # Test different version gives different instance
    repo4 = TestRepository(dataset=dataset4)
    assert repo1 is not repo4
    assert repo3 is not repo4

    TestRepository._instances = {}


def test_different_paths_create_different_instances():
    """Test that datasets with different paths create different singleton instances."""

    class TestRepository(metaclass=SingletonMeta):
        """Test repository class using SingletonMeta."""

        def __init__(self, dataset=None):
            self.dataset = dataset
            self.initialized = True

    # Create datasets with different paths
    dataset1 = Dataset(
        name="test1",
        path_prefix="test/path1",
        version=1,
        adapter=RepositoryOption.in_memory,
        dataset_tables={},
    )

    dataset2 = Dataset(
        name="test2",
        path_prefix="test/path2",
        version=1,
        adapter=RepositoryOption.in_memory,
        dataset_tables={},
    )

    repo1 = TestRepository(dataset=dataset1)
    repo2 = TestRepository(dataset=dataset2)

    # Different paths should give different instances
    assert repo1 is not repo2
    TestRepository._instances = {}


def test_different_versions_create_different_instances():
    """Test that datasets with different versions create different singleton instances."""

    class TestRepository(metaclass=SingletonMeta):
        """Test repository class using SingletonMeta."""

        def __init__(self, dataset=None):
            self.dataset = dataset
            self.initialized = True

    # Create datasets with different versions
    dataset1 = Dataset(
        name="test1",
        path_prefix="test/path",
        version=1,
        adapter=RepositoryOption.in_memory,
        dataset_tables={},
    )

    dataset2 = Dataset(
        name="test2",
        path_prefix="test/path",
        version=2,
        adapter=RepositoryOption.in_memory,
        dataset_tables={},
    )

    repo1 = TestRepository(dataset=dataset1)
    repo2 = TestRepository(dataset=dataset2)

    # Different versions should give different instances
    assert repo1 is not repo2
    TestRepository._instances = {}


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
    TestSingleton._instances = {}


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
    TestSingleton._instances = {}
    AnotherTestSingleton._instances = {}
