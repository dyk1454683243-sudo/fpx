"""
Стресс-тесты Router/ChatRunner.

Проверяем, что диспетчинг сообщений и большое число зарегистрированных
хендлеров не приводят к деградации/некорректному поведению при большом
объёме одновременно обрабатываемых событий.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.runner.subclasses._chat import ChatRunner
from fpx.classes.runner.subclasses.router import Router
from fpx.models.chat import Message
from fpx.utils.storage.memory import MemoryStorage

pytestmark = pytest.mark.stress

N_HANDLERS = 300
N_MESSAGES = 500
N_CHATS = 200


class TestRouterDispatchStress:
    @pytest.mark.asyncio
    async def test_many_registered_handlers_only_first_match_fires(self):
        router = Router()
        call_counts = {i: 0 for i in range(N_HANDLERS)}

        for i in range(N_HANDLERS):

            def make_handler(idx):
                async def handler(msg: Message):
                    call_counts[idx] += 1

                return handler

            router._handlers["message"].append(
                {
                    "function": make_handler(i),
                    "filter_text": None,
                    "contains": None,
                    "regex": None,
                    "custom": None,
                    "mapping": None,
                    "state": None,
                    "ignore_chat_id": None,
                    "ignore_sender": None,
                    "priority": 0,
                }
            )

        runner = MagicMock()
        runner.router = router
        runner._cache = {}
        runner.storage = MemoryStorage()
        runner._account.data.username = "Bot"
        runner._handle_error = AsyncMock()

        chat_runner = ChatRunner(runner)
        msg = Message(node_msg_id=1, sender="User", chat_id="chat-1", text="hello", is_system=False)

        start = time.monotonic()
        await chat_runner._trigger_message_handlers(msg)
        elapsed = time.monotonic() - start

        assert sum(call_counts.values()) == 1, "Должен сработать только первый подходящий хендлер"
        assert call_counts[0] == 1
        assert elapsed < 5, f"Диспетчинг с {N_HANDLERS} хендлерами занял подозрительно долго: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_many_concurrent_chats_processed_without_crosstalk(self):
        router = Router()
        received = []

        @router.on_message()
        async def handler(msg: Message):
            received.append((msg.chat_id, msg.text))

        runner = MagicMock()
        runner.router = router
        runner._cache = {}
        runner.storage = MemoryStorage()
        runner._account.data.username = "Bot"
        runner._handle_error = AsyncMock()

        chat_runner = ChatRunner(runner)
        messages = [
            Message(node_msg_id=i, sender="User", chat_id=f"chat_{i % N_CHATS}", text=f"msg{i}", is_system=False)
            for i in range(N_MESSAGES)
        ]

        await asyncio.gather(*(chat_runner._trigger_message_handlers(m) for m in messages))

        assert len(received) == N_MESSAGES
        assert len(set(chat_id for chat_id, _ in received)) == min(N_CHATS, N_MESSAGES)


class TestChatCacheComparisonStress:
    def test_compare_chat_cache_with_large_dataset(self):
        router = Router()
        runner = MagicMock()
        runner.router = router
        old_msgs = [
            {"sender": f"user{i}", "chat_id": str(i), "last_msg": {"node_id": i, "message": f"old-{i}"}}
            for i in range(2000)
        ]
        new_msgs = [
            {"sender": f"user{i}", "chat_id": str(i), "last_msg": {"node_id": i, "message": f"new-{i}"}}
            for i in range(2000)
        ]
        runner._cache = {"msgs": new_msgs, "old_msgs": old_msgs}
        chat_runner = ChatRunner(runner)

        start = time.monotonic()
        result = chat_runner._compare_chat_cache()
        elapsed = time.monotonic() - start

        assert len(result) == 2000
        assert elapsed < 5, f"Сравнение 2000 сообщений заняло подозрительно долго: {elapsed:.2f}s"
