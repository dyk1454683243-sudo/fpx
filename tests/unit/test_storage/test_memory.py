"""Тесты MemoryStorage — хранение стейта FSM в памяти."""
import pytest

from fpx.utils.storage.memory import MemoryStorage


class TestMemoryStorage:
    @pytest.mark.asyncio
    async def test_set_and_get_state(self):
        storage = MemoryStorage()
        await storage.set_state("chat_1", "waiting_name")
        assert await storage.get_state("chat_1") == "waiting_name"

    @pytest.mark.asyncio
    async def test_get_state_unknown_chat_returns_none(self):
        storage = MemoryStorage()
        assert await storage.get_state("unknown") is None

    @pytest.mark.asyncio
    async def test_set_state_accepts_int_chat_id(self):
        storage = MemoryStorage()
        await storage.set_state(123, "state")
        assert await storage.get_state(123) == "state"
        assert await storage.get_state("123") == "state"

    @pytest.mark.asyncio
    async def test_update_and_get_data(self):
        storage = MemoryStorage()
        await storage.update_data("chat_1", name="Иван")
        await storage.update_data("chat_1", age="25")
        assert await storage.get_data("chat_1") == {"name": "Иван", "age": "25"}

    @pytest.mark.asyncio
    async def test_get_data_unknown_chat_returns_empty_dict(self):
        storage = MemoryStorage()
        assert await storage.get_data("unknown") == {}

    @pytest.mark.asyncio
    async def test_clear_state_removes_everything(self):
        storage = MemoryStorage()
        await storage.set_state("chat_1", "state")
        await storage.update_data("chat_1", key="val")
        await storage.clear_state("chat_1")
        assert await storage.get_state("chat_1") is None
        assert await storage.get_data("chat_1") == {}

    @pytest.mark.asyncio
    async def test_clear_state_unknown_chat_does_not_raise(self):
        storage = MemoryStorage()
        await storage.clear_state("unknown")  # не должно вызывать ошибку

    @pytest.mark.asyncio
    async def test_overwrite_state(self):
        storage = MemoryStorage()
        await storage.set_state("chat_1", "state1")
        await storage.set_state("chat_1", "state2")
        assert await storage.get_state("chat_1") == "state2"

    @pytest.mark.asyncio
    async def test_chats_are_isolated(self):
        storage = MemoryStorage()
        await storage.set_state("chat_1", "A")
        await storage.set_state("chat_2", "B")
        assert await storage.get_state("chat_1") == "A"
        assert await storage.get_state("chat_2") == "B"
