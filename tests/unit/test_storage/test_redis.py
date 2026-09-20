"""Тесты RedisStorage.

Пакет `redis` не является жёсткой зависимостью fpx (устанавливается как extra
`fpx-engine[redis]`), поэтому тесты подменяют `redis.asyncio.Redis` фейковым
асинхронным клиентом на основе словаря, чтобы не требовать реального сервера Redis.
"""

import json
import sys
import types
from unittest.mock import AsyncMock

import pytest


class FakeAsyncRedis:
    """Мини-имитация redis.asyncio.Redis, достаточная для RedisStorage."""

    def __init__(self):
        self._store = {}

    @classmethod
    def from_url(cls, url, decode_responses=True):
        instance = cls()
        instance.url = url
        return instance

    async def set(self, key, value):
        self._store[key] = value
        return True

    async def get(self, key):
        return self._store.get(key)

    async def delete(self, key):
        return self._store.pop(key, None) is not None


@pytest.fixture
def fake_redis_module(monkeypatch):
    """Инжектирует фейковый модуль redis.asyncio в sys.modules."""
    redis_pkg = types.ModuleType("redis")
    redis_asyncio_pkg = types.ModuleType("redis.asyncio")
    redis_asyncio_pkg.Redis = FakeAsyncRedis
    redis_pkg.asyncio = redis_asyncio_pkg
    monkeypatch.setitem(sys.modules, "redis", redis_pkg)
    monkeypatch.setitem(sys.modules, "redis.asyncio", redis_asyncio_pkg)
    yield


@pytest.fixture
def redis_storage(fake_redis_module):
    from fpx.utils.storage.redis import RedisStorage

    return RedisStorage(url="redis://fake:6379", prefix="test")


class TestRedisStorageImportGuard:
    def test_missing_redis_package_raises_import_error(self, monkeypatch):
        import fpx.utils.storage.redis as redis_module

        monkeypatch.setitem(sys.modules, "redis", None)
        monkeypatch.setitem(sys.modules, "redis.asyncio", None)
        with pytest.raises(ImportError) as exc:
            redis_module.RedisStorage()
        assert isinstance(exc.value.__cause__, ImportError)


class TestRedisStorageKeyBuilding:
    def test_key_uses_prefix(self, redis_storage):
        assert redis_storage._key("777") == "test:fsm:777"


class TestRedisStorageOperations:
    @pytest.mark.asyncio
    async def test_set_and_get_state(self, redis_storage):
        await redis_storage.set_state("chat_1", "waiting")
        assert await redis_storage.get_state("chat_1") == "waiting"

    @pytest.mark.asyncio
    async def test_get_state_missing_key_returns_none(self, redis_storage):
        assert await redis_storage.get_state("unknown") is None

    @pytest.mark.asyncio
    async def test_update_and_get_data(self, redis_storage):
        await redis_storage.update_data("chat_1", name="Иван")
        await redis_storage.update_data("chat_1", age="25")
        data = await redis_storage.get_data("chat_1")
        assert data == {"name": "Иван", "age": "25"}

    @pytest.mark.asyncio
    async def test_get_data_missing_key_returns_empty_dict(self, redis_storage):
        assert await redis_storage.get_data("unknown") == {}

    @pytest.mark.asyncio
    async def test_state_and_data_survive_together(self, redis_storage):
        await redis_storage.set_state("chat_1", "s1")
        await redis_storage.update_data("chat_1", foo="bar")
        assert await redis_storage.get_state("chat_1") == "s1"
        assert await redis_storage.get_data("chat_1") == {"foo": "bar"}

    @pytest.mark.asyncio
    async def test_clear_state_removes_key(self, redis_storage):
        await redis_storage.set_state("chat_1", "s1")
        await redis_storage.clear_state("chat_1")
        assert await redis_storage.get_state("chat_1") is None
        assert await redis_storage.get_data("chat_1") == {}

    @pytest.mark.asyncio
    async def test_int_chat_id_normalized(self, redis_storage):
        await redis_storage.set_state(555, "s")
        assert await redis_storage.get_state("555") == "s"

    @pytest.mark.asyncio
    async def test_raw_json_shape(self, redis_storage):
        await redis_storage.set_state("chat_1", "s1")
        raw = await redis_storage._redis.get(redis_storage._key("chat_1"))
        parsed = json.loads(raw)
        assert parsed == {"state": "s1", "data": {}}

    @pytest.mark.asyncio
    async def test_update_data_is_not_race_safe_by_design(self, redis_storage, monkeypatch):
        """Документированное поведение: update_data читает-потом-пишет, без атомарности."""
        redis_storage._redis.get = AsyncMock(wraps=redis_storage._redis.get)
        await redis_storage.update_data("chat_1", a="1")
        assert redis_storage._redis.get.await_count >= 1
