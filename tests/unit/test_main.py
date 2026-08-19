"""Тесты FunPayTools — точка входа в библиотеку, инициализация клиента/раннера."""
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from fpx.classes.account.account import Account
from fpx.classes.runner.runner import Runner
from fpx.main import FunPayTools
from fpx.utils.storage.memory import MemoryStorage


class TestInit:
    def test_default_http_client_is_created_with_cookies(self):
        tools = FunPayTools("gkey", "gseal")
        assert tools._client.cookies["golden_key"] == "gkey"
        assert tools._client.cookies["golden_seal"] == "gseal"
        assert isinstance(tools.account, Account)
        assert isinstance(tools.runner, Runner)
        assert tools.router is tools.runner.router

    def test_default_storage_is_memory_storage(self):
        tools = FunPayTools("gkey", "gseal")
        assert isinstance(tools.storage, MemoryStorage)
        assert tools.runner.storage is tools.storage

    def test_custom_storage_is_used(self):
        custom_storage = MemoryStorage()
        tools = FunPayTools("gkey", "gseal", storage=custom_storage)
        assert tools.storage is custom_storage
        assert tools.runner.storage is custom_storage

    def test_custom_http_client_gets_cookies_and_headers_merged(self):
        http_client = httpx.AsyncClient()
        tools = FunPayTools("gkey", "gseal", http_client=http_client)
        assert tools._client is http_client
        assert http_client.cookies["golden_key"] == "gkey"

    def test_proxy_and_http_client_together_raises(self):
        http_client = httpx.AsyncClient()
        with pytest.raises(ValueError):
            FunPayTools("gkey", "gseal", proxy="http://127.0.0.1:8080", http_client=http_client)

    def test_proxy_alone_builds_client_with_mounts(self):
        tools = FunPayTools("gkey", "gseal", proxy="http://127.0.0.1:8080")
        assert tools._client is not None

    def test_request_engine_linked_to_runner(self):
        tools = FunPayTools("gkey", "gseal")
        assert tools.account._request_engine.runner is tools.runner


class TestShutdown:
    @pytest.mark.asyncio
    async def test_shutdown_stops_runner_and_closes_client(self):
        tools = FunPayTools("gkey", "gseal")
        tools.runner.is_running = True
        await tools.shutdown()
        assert tools.runner.is_running is False
        assert tools._client.is_closed is True

    @pytest.mark.asyncio
    async def test_shutdown_idempotent_when_already_closed(self):
        tools = FunPayTools("gkey", "gseal")
        await tools.shutdown()
        # повторный вызов не должен упасть
        await tools.shutdown()

    @pytest.mark.asyncio
    async def test_async_context_manager_calls_shutdown(self):
        tools = FunPayTools("gkey", "gseal")
        async with tools as t:
            assert t is tools
        assert tools._client.is_closed is True
