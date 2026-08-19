"""Тесты FileStorage — персистентное хранилище FSM на файловой системе."""
import json

import pytest

from fpx.utils.storage.file import FileStorage


@pytest.fixture
def storage_path(tmp_path):
    return str(tmp_path / "fsm_storage.json")


class TestFileStorageInit:
    def test_init_without_existing_file(self, storage_path):
        storage = FileStorage(storage_path)
        assert storage._states == {}
        assert storage.file_path == storage_path

    def test_init_loads_existing_valid_file(self, storage_path):
        data = {"1": {"state": "s", "data": {"k": "v"}}}
        with open(storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        storage = FileStorage(storage_path)
        assert storage._states == data

    def test_init_with_corrupted_file_resets_to_empty(self, storage_path):
        with open(storage_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        storage = FileStorage(storage_path)
        assert storage._states == {}


class TestFileStorageOperations:
    @pytest.mark.asyncio
    async def test_set_and_get_state_persists_to_disk(self, storage_path):
        storage = FileStorage(storage_path)
        await storage.set_state("chat_1", "waiting")
        assert await storage.get_state("chat_1") == "waiting"
        with open(storage_path, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["chat_1"]["state"] == "waiting"

    @pytest.mark.asyncio
    async def test_get_state_unknown_returns_none(self, storage_path):
        storage = FileStorage(storage_path)
        assert await storage.get_state("unknown") is None

    @pytest.mark.asyncio
    async def test_update_and_get_data(self, storage_path):
        storage = FileStorage(storage_path)
        await storage.update_data("chat_1", name="Иван")
        await storage.update_data("chat_1", age="25")
        assert await storage.get_data("chat_1") == {"name": "Иван", "age": "25"}

    @pytest.mark.asyncio
    async def test_get_data_unknown_returns_empty(self, storage_path):
        storage = FileStorage(storage_path)
        assert await storage.get_data("unknown") == {}

    @pytest.mark.asyncio
    async def test_clear_state_removes_chat_and_persists(self, storage_path):
        storage = FileStorage(storage_path)
        await storage.set_state("chat_1", "state")
        await storage.clear_state("chat_1")
        assert await storage.get_state("chat_1") is None
        with open(storage_path, encoding="utf-8") as f:
            saved = json.load(f)
        assert "chat_1" not in saved

    @pytest.mark.asyncio
    async def test_clear_state_unknown_chat_noop(self, storage_path):
        storage = FileStorage(storage_path)
        await storage.clear_state("unknown")  # не должно упасть, файл не создастся

    @pytest.mark.asyncio
    async def test_reloading_storage_from_disk_keeps_data(self, storage_path):
        storage = FileStorage(storage_path)
        await storage.set_state("chat_1", "s1")
        await storage.update_data("chat_1", foo="bar")

        reloaded = FileStorage(storage_path)
        assert await reloaded.get_state("chat_1") == "s1"
        assert await reloaded.get_data("chat_1") == {"foo": "bar"}

    @pytest.mark.asyncio
    async def test_int_chat_id_is_normalized_to_str(self, storage_path):
        storage = FileStorage(storage_path)
        await storage.set_state(42, "s")
        assert await storage.get_state("42") == "s"
