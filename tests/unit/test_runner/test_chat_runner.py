"""Тесты ChatRunner — фильтры сообщений, команды, FSM-состояния, диспетчинг."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from fpx.classes.runner.subclasses._chat import ChatRunner
from fpx.classes.runner.subclasses.router import Router
from fpx.models.chat import Message
from fpx.utils.storage.memory import MemoryStorage


@pytest.fixture
def runner():
    r = MagicMock()
    r._cache = {'msgs': [], 'old_msgs': []}
    r._account.data.username = "Bot"
    r._handle_error = AsyncMock()
    r.storage = MemoryStorage()
    r.router = Router()
    return r


@pytest.fixture
def chat_runner(runner):
    return ChatRunner(runner)


def make_message(text="hello", sender="User", chat_id="chat-1"):
    return Message(node_msg_id=1, sender=sender, chat_id=chat_id, text=text, is_system=False)


class TestCompareChatCache:
    def test_no_changes_returns_empty(self, chat_runner, runner):
        runner._cache['msgs'] = runner._cache['old_msgs'] = [
            {'sender': 'A', 'chat_id': '1', 'last_msg': {'node_id': 1, 'message': 'hi'}}
        ]
        assert chat_runner._compare_chat_cache() == []

    def test_new_message_detected(self, chat_runner, runner):
        runner._cache['old_msgs'] = []
        runner._cache['msgs'] = [
            {'sender': 'A', 'chat_id': '1', 'last_msg': {'node_id': 1, 'message': 'привет'}}
        ]
        result = chat_runner._compare_chat_cache()
        assert len(result) == 1
        assert isinstance(result[0], Message)
        assert result[0].text == 'привет'

    def test_stop_words_are_filtered_out(self, chat_runner, runner):
        runner._cache['old_msgs'] = []
        runner._cache['msgs'] = [
            {'sender': 'A', 'chat_id': '1', 'last_msg': {'node_id': 1, 'message': 'Покупатель оплатил заказ'}}
        ]
        assert chat_runner._compare_chat_cache() == []


class TestUpdateChatCache:
    @pytest.mark.asyncio
    async def test_moves_msgs_to_old_and_fetches_new(self, chat_runner, runner):
        chat = MagicMock(username="Bob", id="1", node_msg_id=5, last_msg="hi")
        runner._account.chat.get_chats = AsyncMock(return_value=[chat])
        runner._cache['msgs'] = [{'existing': True}]
        await chat_runner._update_chat_cache()
        assert runner._cache['old_msgs'] == [{'existing': True}]
        assert runner._cache['msgs'][0]['sender'] == 'Bob'


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_no_text_returns_false(self, chat_runner, runner):
        msg = make_message(text="")
        assert await chat_runner._process_message(msg, None) is False

    @pytest.mark.asyncio
    async def test_matches_command_without_args(self, chat_runner, runner):
        called = {}

        async def handler(message: Message):
            called['ok'] = True
        runner.router._handlers['commands'] = [{'command': {'/start': handler}}]
        msg = make_message(text="/start")
        result = await chat_runner._process_message(msg, "state_ctx")
        assert result is True
        assert called.get('ok') is True

    @pytest.mark.asyncio
    async def test_missing_required_text_arg_triggers_error_handler(self, chat_runner, runner):
        async def handler(message: Message, name: str):
            pass
        runner.router._handlers['commands'] = [{'command': {'/greet': handler}}]
        msg = make_message(text="/greet")
        result = await chat_runner._process_message(msg, "state_ctx")
        assert result is False
        runner._handle_error.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_command_with_provided_args_invokes(self, chat_runner, runner):
        received = {}

        async def handler(message: Message, name: str):
            received['name'] = name
        runner.router._handlers['commands'] = [{'command': {'/greet': handler}}]
        msg = make_message(text="/greet Bob")
        result = await chat_runner._process_message(msg, "state_ctx")
        assert result is True
        assert received['name'] == "bob"

    @pytest.mark.asyncio
    async def test_no_matching_command_returns_false(self, chat_runner, runner):
        runner.router._handlers['commands'] = [{'command': {'/other': AsyncMock()}}]
        msg = make_message(text="/greet")
        assert await chat_runner._process_message(msg, "state_ctx") is False


class TestFilters:
    def test_text_filter_none_matches_all(self, chat_runner):
        assert chat_runner._check_text_filter("anything", None, None) is True

    def test_text_filter_prefix_match(self, chat_runner):
        assert chat_runner._check_text_filter("hello world", "hello", None) is True
        assert chat_runner._check_text_filter("goodbye", "hello", None) is False

    def test_contains_filter_none_matches_all(self, chat_runner):
        assert chat_runner._check_contains_filter("text", None) is True

    def test_contains_filter_single_string(self, chat_runner):
        assert chat_runner._check_contains_filter("hello world", "world") is True
        assert chat_runner._check_contains_filter("hello world", "xyz") is False

    def test_contains_filter_list(self, chat_runner):
        assert chat_runner._check_contains_filter("hello world", ["abc", "world"]) is True

    def test_regex_filter_none_matches_all(self, chat_runner):
        assert chat_runner._check_regex("text", None) is True

    def test_regex_filter_matches(self, chat_runner):
        assert chat_runner._check_regex("order #123", r"\d+") is True
        assert chat_runner._check_regex("no digits", r"\d+") is False

    def test_regex_filter_list(self, chat_runner):
        assert chat_runner._check_regex("hello", ["xyz", "hel+o"]) is True

    def test_chat_id_check_none_always_true(self, chat_runner):
        msg = make_message(chat_id="1")
        assert chat_runner._chat_id_check(msg, None) is True

    def test_chat_id_check_excludes_matching_id(self, chat_runner):
        msg = make_message(chat_id="1")
        assert chat_runner._chat_id_check(msg, "1") is False
        assert chat_runner._chat_id_check(msg, ["2", "3"]) is True

    def test_sender_check_none_always_true(self, chat_runner):
        msg = make_message(sender="Bob")
        assert chat_runner._sender_check(msg, None) is True

    def test_sender_check_excludes_matching_sender(self, chat_runner):
        msg = make_message(sender="Bob")
        assert chat_runner._sender_check(msg, "Bob") is False
        assert chat_runner._sender_check(msg, ["Alice"]) is True

    @pytest.mark.asyncio
    async def test_custom_check_none_always_true(self, chat_runner):
        assert await chat_runner._custom_check(make_message(), None) is True

    @pytest.mark.asyncio
    async def test_custom_check_sync_function(self, chat_runner):
        assert await chat_runner._custom_check(make_message(text="x"), lambda m: m.text == "x") is True
        assert await chat_runner._custom_check(make_message(text="y"), lambda m: m.text == "x") is False

    @pytest.mark.asyncio
    async def test_custom_check_async_function(self, chat_runner):
        async def check(m):
            return True
        assert await chat_runner._custom_check(make_message(), check) is True

    @pytest.mark.asyncio
    async def test_check_filters_all_pass(self, chat_runner):
        msg = make_message(text="hello world", sender="Bob", chat_id="1")
        handler = {
            'filter_text': "hello", 'mapping': None, 'contains': "world",
            'regex': None, 'ignore_chat_id': None, 'ignore_sender': None, 'custom': None
        }
        assert await chat_runner._check_filters(msg, handler) is True

    @pytest.mark.asyncio
    async def test_check_filters_fails_on_text_filter(self, chat_runner):
        msg = make_message(text="bye", sender="Bob", chat_id="1")
        handler = {
            'filter_text': "hello", 'mapping': None, 'contains': None,
            'regex': None, 'ignore_chat_id': None, 'ignore_sender': None, 'custom': None
        }
        assert await chat_runner._check_filters(msg, handler) is False


class TestGetLastId:
    def test_returns_none_by_default(self, chat_runner):
        assert chat_runner.get_last_id("chat-1") is None

    def test_returns_stored_value(self, chat_runner):
        chat_runner._chat_last_ids["chat-1"] = "5"
        assert chat_runner.get_last_id("chat-1") == "5"


class TestTriggerMessageHandlers:
    @pytest.mark.asyncio
    async def test_fetches_username_when_missing(self, chat_runner, runner):
        runner._account.data.username = None

        async def fetch():
            runner._account.data.username = "Bot"
        runner._account.profile.get_user_data = AsyncMock(side_effect=fetch)
        msg = make_message(sender="User")
        await chat_runner._trigger_message_handlers(msg)
        runner._account.profile.get_user_data.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ignores_own_messages(self, chat_runner, runner):
        msg = make_message(sender="Bot")
        handler = AsyncMock()
        runner.router._handlers['message'] = [{
            'state': None, 'filter_text': None, 'mapping': None, 'contains': None,
            'regex': None, 'ignore_chat_id': None, 'ignore_sender': None, 'custom': None,
            'function': handler,
        }]
        await chat_runner._trigger_message_handlers(msg)
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatches_matching_message_handler(self, chat_runner, runner):
        handler = AsyncMock()
    
        async def fake_handler(message: Message, **kwargs):
            await handler(message, **kwargs)

        runner.router._handlers['message'] = [{
            'state': None, 'filter_text': None, 'mapping': None, 'contains': None,
            'regex': None, 'ignore_chat_id': None, 'ignore_sender': None, 'custom': None,
            'function': fake_handler,
        }]
        msg = make_message(sender="User", text="hi")
        await chat_runner._trigger_message_handlers(msg)
        
        handler.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_state_mismatch_skips_handler(self, chat_runner, runner):
        handler = AsyncMock()
        runner.router._handlers['message'] = [{
            'state': "waiting_name", 'filter_text': None, 'mapping': None, 'contains': None,
            'regex': None, 'ignore_chat_id': None, 'ignore_sender': None, 'custom': None,
            'function': handler,
        }]
        msg = make_message(sender="User", text="hi")
        await chat_runner._trigger_message_handlers(msg)
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_mapping_sends_automated_reply_and_still_invokes_handler(self, chat_runner, runner):
        msg = make_message(sender="User", text="привет всем")
        msg._client = MagicMock()
        msg._client._account.chat.send_message = AsyncMock()
        
        handler_func = AsyncMock()
        

        async def fake_handler(message: Message, **kwargs):
            await handler_func(message, **kwargs)
            
        runner.router._handlers['message'] = [{
            'state': None, 'filter_text': None,
            'mapping': {'привет': 'Здравствуйте, {sender}!'},
            'contains': None, 'regex': None, 'ignore_chat_id': None,
            'ignore_sender': None, 'custom': None, 
            'function': fake_handler, 
        }]
        await chat_runner._trigger_message_handlers(msg)
    
        msg._client._account.chat.send_message.assert_awaited_once()
        handler_func.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_mapping_no_trigger_match_skips_handler(self, chat_runner, runner):
        msg = make_message(sender="User", text="случайный текст")
        handler_func = AsyncMock()
        runner.router._handlers['message'] = [{
            'state': None, 'filter_text': None,
            'mapping': {'привет': 'Здравствуйте!'},
            'contains': None, 'regex': None, 'ignore_chat_id': None,
            'ignore_sender': None, 'custom': None, 'function': handler_func,
        }]
        await chat_runner._trigger_message_handlers(msg)
        handler_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_exception_in_process_message_handled(self, chat_runner, runner):
        async def bad_handler(message, state, args=None):
            raise ValueError("boom")
        runner.router._handlers['commands'] = [{'command': {'/x': bad_handler}}]
        runner.router.invoke = AsyncMock(side_effect=ValueError("boom"))
        msg = make_message(sender="User", text="/x")
        await chat_runner._trigger_message_handlers(msg)
        runner._handle_error.assert_awaited_once()


class TestCheckChats:
    @pytest.mark.asyncio
    async def test_no_new_chats_does_nothing(self, chat_runner, runner):
        runner._account.chat.get_chats = AsyncMock(return_value=[])
        await chat_runner._check_chats()
        # не должно упасть

    @pytest.mark.asyncio
    async def test_processes_new_chat_messages(self, chat_runner, runner):
        chat = MagicMock(username="Alice", id="chat-1", node_msg_id=10, last_msg="Привет!")
        runner._account.chat.get_chats = AsyncMock(return_value=[chat])

        msg = Message(node_msg_id=11, sender="Alice", chat_id="chat-1", text="Привет!", is_system=False)
        chat_data = MagicMock(last_messages=[msg])
        runner._account.chat.get_chat_data = AsyncMock(return_value=chat_data)
        runner._account.data.username = "Bot"

        await chat_runner._check_chats()
        runner._account.chat.get_chat_data.assert_awaited_once()
        assert chat_runner.get_last_id("chat-1") == "11"
