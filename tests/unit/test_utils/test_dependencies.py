"""Тесты Dependency — обёртка для DI в хендлерах роутера."""
from fpx.utils.dependencies import Dependency


class TestDependency:
    def test_stores_callable(self):
        def my_dep():
            return 42
        dep = Dependency(my_dep)
        assert dep.dependency is my_dep
        assert dep.dependency() == 42

    def test_stores_lambda(self):
        dep = Dependency(lambda: "value")
        assert dep.dependency() == "value"

    def test_stores_async_callable(self):
        async def async_dep():
            return "async-value"
        dep = Dependency(async_dep)
        assert dep.dependency is async_dep
