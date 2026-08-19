"""
Стресс-тесты хранилищ FSM.

Цель — убедиться, что MemoryStorage и FileStorage не теряют и не путают данные
при большом количестве чатов и высокой конкурентности операций записи/чтения.
Эти тесты медленнее unit-тестов и не входят в дефолтный `pytest` без явного
указания директории tests/stress (см. tests/pytest.ini и tests/run_tests.py).
"""
import asyncio
import time

import pytest

from fpx.utils.storage.file import FileStorage
from fpx.utils.storage.memory import MemoryStorage

pytestmark = pytest.mark.stress

N_CHATS = 2000
N_CONCURRENT_WORKERS = 200


class TestMemoryStorageStress:
    @pytest.mark.asyncio
    async def test_many_chats_no_cross_contamination(self):
        storage = MemoryStorage()
        for i in range(N_CHATS):
            await storage.set_state(f"chat_{i}", f"state_{i}")
            await storage.update_data(f"chat_{i}", index=str(i))

        for i in range(N_CHATS):
            assert await storage.get_state(f"chat_{i}") == f"state_{i}"
            assert await storage.get_data(f"chat_{i}") == {"index": str(i)}

    @pytest.mark.asyncio
    async def test_high_concurrency_set_get(self):
        storage = MemoryStorage()

        async def worker(i):
            chat_id = f"chat_{i % 50}"
            await storage.set_state(chat_id, f"s{i}")
            await storage.update_data(chat_id, last_writer=str(i))
            return await storage.get_state(chat_id)

        results = await asyncio.gather(*(worker(i) for i in range(N_CONCURRENT_WORKERS)))
        # каждый воркер должен получить какое-то валидное состояние, без исключений
        assert all(r is not None for r in results)
        assert len(results) == N_CONCURRENT_WORKERS

    @pytest.mark.asyncio
    async def test_clear_all_chats_leaves_storage_empty(self):
        storage = MemoryStorage()
        for i in range(N_CHATS):
            await storage.set_state(f"chat_{i}", "s")
        for i in range(N_CHATS):
            await storage.clear_state(f"chat_{i}")
        for i in range(N_CHATS):
            assert await storage.get_state(f"chat_{i}") is None


class TestFileStorageStress:
    @pytest.mark.asyncio
    async def test_many_writes_persist_correctly(self, tmp_path):
        storage = FileStorage(str(tmp_path / "stress_storage.json"))
        for i in range(N_CHATS):
            await storage.set_state(f"chat_{i}", f"state_{i}")

        # перечитываем с диска и проверяем целостность данных
        reloaded = FileStorage(str(tmp_path / "stress_storage.json"))
        for i in range(N_CHATS):
            assert await reloaded.get_state(f"chat_{i}") == f"state_{i}"

    @pytest.mark.asyncio
    async def test_concurrent_writes_do_not_corrupt_file(self, tmp_path):
        storage = FileStorage(str(tmp_path / "stress_concurrent.json"))

        async def worker(i):
            await storage.set_state(f"chat_{i}", f"s{i}")
            await storage.update_data(f"chat_{i}", n=str(i))

        await asyncio.gather(*(worker(i) for i in range(N_CONCURRENT_WORKERS)))

        for i in range(N_CONCURRENT_WORKERS):
            assert await storage.get_state(f"chat_{i}") == f"s{i}"

    @pytest.mark.asyncio
    async def test_write_throughput_is_reasonable(self, tmp_path):
        """
        Не строгий бенчмарк, а защита от явных регрессий производительности:
        1000 последовательных записей должны укладываться в разумное время.
        """
        storage = FileStorage(str(tmp_path / "throughput.json"))
        start = time.monotonic()
        for i in range(1000):
            await storage.set_state(f"chat_{i}", "s")
        elapsed = time.monotonic() - start
        assert elapsed < 20, f"Запись 1000 состояний заняла подозрительно долго: {elapsed:.2f}s"
