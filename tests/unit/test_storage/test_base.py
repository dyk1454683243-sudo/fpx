"""Тесты BaseStorage — базовый интерфейс хранилища FSM."""
import pytest

from fpx.utils.storage.base import BaseStorage


class TestBaseStorage:
    @pytest.mark.asyncio
    async def test_set_state_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await BaseStorage().set_state("1", "state")

    @pytest.mark.asyncio
    async def test_get_state_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await BaseStorage().get_state("1")

    @pytest.mark.asyncio
    async def test_update_data_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await BaseStorage().update_data("1", key="value")

    @pytest.mark.asyncio
    async def test_get_data_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await BaseStorage().get_data("1")

    @pytest.mark.asyncio
    async def test_clear_state_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await BaseStorage().clear_state("1")
