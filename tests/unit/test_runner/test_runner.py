"""Тесты Runner — оркестрация фонового опроса, кеш, обработка ошибок."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from fpx.classes.runner.runner import Runner
from fpx.utils import errors as fpx_err


@pytest.fixture
def account():
    return MagicMock()


@pytest.fixture
def runner(account):
    return Runner(account)


class TestRunnerInit:
    def test_default_cache_shape(self, runner):
        assert runner._cache["msgs"] == []
        assert runner._cache["orders"] == []
        assert runner._cache["reviews"] == []
        assert runner.is_running is True
        assert runner._cache_is_updated is False
        assert runner.storage is None

    def test_subrunners_reference_self(self, runner):
        assert runner._chat.runner is runner
        assert runner._order.runner is runner
        assert runner._review.runner is runner
        assert runner._category.runner is runner


class TestWarmUp:
    @pytest.mark.asyncio
    async def test_success_marks_cache_updated_and_runs_startup_handlers(self, runner, account):
        account.profile.get_user_data = AsyncMock()
        runner._chat._update_chat_cache = AsyncMock()
        runner._order._update_order_cache = AsyncMock()
        runner._review._update_review_cache = AsyncMock()
        started = []

        @runner.router.on_startup()
        async def on_start():
            started.append(True)

        await runner._warm_up(None, None)
        assert runner._cache_is_updated is True
        assert started == [True]

    @pytest.mark.asyncio
    async def test_watch_lots_and_chips_are_checked(self, runner, account):
        account.profile.get_user_data = AsyncMock()
        runner._category._check_lot_categories = AsyncMock()
        runner._category._check_chip_categories = AsyncMock()
        runner._chat._update_chat_cache = AsyncMock()
        runner._order._update_order_cache = AsyncMock()
        runner._review._update_review_cache = AsyncMock()
        await runner._warm_up(["cat-1"], ["chip-1"])
        runner._category._check_lot_categories.assert_awaited_once_with(["cat-1"])
        runner._category._check_chip_categories.assert_awaited_once_with(["chip-1"])

    @pytest.mark.asyncio
    async def test_failure_marks_cache_not_updated_and_calls_error_handler(self, runner, account):
        account.profile.get_user_data = AsyncMock()
        runner._chat._update_chat_cache = AsyncMock(side_effect=Exception("boom"))
        runner._order._update_order_cache = AsyncMock()
        runner._review._update_review_cache = AsyncMock()
        runner._handle_error = AsyncMock()
        await runner._warm_up(None, None)
        assert runner._cache_is_updated is False
        runner._handle_error.assert_awaited_once()


class TestCacheRunner:
    @pytest.mark.asyncio
    async def test_calls_warm_up_when_not_updated(self, runner):
        runner._warm_up = AsyncMock()
        await runner._cache_runner(None, None)
        runner._warm_up.assert_awaited_once_with(None, None)

    @pytest.mark.asyncio
    async def test_checks_updates_when_cache_already_warm(self, runner):
        runner._cache_is_updated = True
        runner._chat._check_chats = AsyncMock()
        runner._order._check_orders = AsyncMock()
        runner._review._check_reviews = AsyncMock()
        await runner._cache_runner(None, None)
        runner._chat._check_chats.assert_awaited_once()
        runner._order._check_orders.assert_awaited_once()
        runner._review._check_reviews.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_partial_failure_still_calls_others_and_reports_error(self, runner):
        runner._cache_is_updated = True
        runner._chat._check_chats = AsyncMock(side_effect=Exception("boom"))
        runner._order._check_orders = AsyncMock()
        runner._review._check_reviews = AsyncMock()
        runner._handle_error = AsyncMock()
        await runner._cache_runner(None, None)
        runner._order._check_orders.assert_awaited_once()
        runner._handle_error.assert_awaited_once()


class TestHandleError:
    @pytest.mark.asyncio
    async def test_calls_async_error_handlers(self, runner):
        called = []

        @runner.router.on_error()
        async def on_error(event, exc):
            called.append((event, exc))

        exc = ValueError("boom")
        await runner._handle_error("event", exc)
        assert called == [("event", exc)]

    @pytest.mark.asyncio
    async def test_calls_sync_error_handlers(self, runner):
        called = []

        @runner.router.on_error()
        def on_error(event, exc):
            called.append((event, exc))

        await runner._handle_error(None, ValueError("boom"))
        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_no_handlers_does_not_raise(self, runner):
        await runner._handle_error(None, ValueError("boom"))


class TestRunLoop:
    @pytest.mark.asyncio
    async def test_stops_when_is_running_false(self, runner, monkeypatch):
        runner.is_running = False
        runner._cache_runner = AsyncMock()
        await runner._run_loop(1)
        runner._cache_runner.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_error_sleeps_60_then_stops(self, runner, monkeypatch):
        sleep_mock = AsyncMock()
        monkeypatch.setattr("asyncio.sleep", sleep_mock)

        call_count = {"n": 0}

        async def cache_runner(*args):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise fpx_err.FpxRequestError("boom")
            runner.is_running = False

        runner._cache_runner = cache_runner
        await runner._run_loop(3)
        sleep_mock.assert_any_call(60)

    @pytest.mark.asyncio
    async def test_account_error_sleeps_5_and_continues(self, runner, monkeypatch):
        sleep_mock = AsyncMock()
        monkeypatch.setattr("asyncio.sleep", sleep_mock)
        call_count = {"n": 0}

        async def cache_runner(*args):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise fpx_err.FpxAccountError("boom")
            runner.is_running = False

        runner._cache_runner = cache_runner
        await runner._run_loop(3)
        sleep_mock.assert_any_call(5)

    @pytest.mark.asyncio
    async def test_httpx_error_sleeps_timer(self, runner, monkeypatch):
        sleep_mock = AsyncMock()
        monkeypatch.setattr("asyncio.sleep", sleep_mock)
        call_count = {"n": 0}

        async def cache_runner(*args):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise httpx.ConnectError("boom")
            runner.is_running = False

        runner._cache_runner = cache_runner
        await runner._run_loop(7)
        sleep_mock.assert_any_call(7)

    @pytest.mark.asyncio
    async def test_unknown_exception_wrapped_in_critical_error(self, runner):
        async def cache_runner(*args):
            raise ValueError("unexpected")

        runner._cache_runner = cache_runner
        with pytest.raises(fpx_err.FpxCriticalRunnerError):
            await runner._run_loop(1)


class TestStartPolling:
    @pytest.mark.asyncio
    async def test_background_mode_returns_task(self, runner, monkeypatch):
        runner._run_loop = AsyncMock()
        task = await runner.start_polling(timer=1, is_background=True)
        assert isinstance(task, asyncio.Task)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_foreground_mode_awaits_run_loop(self, runner):
        runner._run_loop = AsyncMock()
        await runner.start_polling(timer=1, is_background=False)
        runner._run_loop.assert_awaited_once_with(1, None, None)


class TestIdle:
    @pytest.mark.asyncio
    async def test_idle_sleeps_forever(self, runner, monkeypatch):
        sleep_mock = AsyncMock(side_effect=[None, asyncio.CancelledError()])
        monkeypatch.setattr("asyncio.sleep", sleep_mock)
        with pytest.raises(asyncio.CancelledError):
            await runner.idle()
        assert sleep_mock.await_count == 2
