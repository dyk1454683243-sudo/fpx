from typing import Any, cast

from .base import BaseStorage


class MemoryStorage(BaseStorage):
    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}

    def _init_chat(self, chat_id: str) -> None:
        if chat_id not in self._states:
            self._states[chat_id] = {"state": None, "data": {}}

    async def set_state(self, chat_id: str | int, state: str | None) -> None:
        chat_id = str(chat_id)
        self._init_chat(chat_id)
        self._states[chat_id]["state"] = state

    async def get_state(self, chat_id: str | int) -> str | None:
        return self._states.get(str(chat_id), {}).get("state")

    async def update_data(self, chat_id: str | int, **kwargs: Any) -> None:
        chat_id = str(chat_id)
        self._init_chat(chat_id)
        self._states[chat_id]["data"].update(kwargs)

    async def get_data(self, chat_id: str | int) -> dict[str, Any]:
        return cast(dict[str, Any], self._states.get(str(chat_id), {}).get("data", {}))

    async def clear_state(self, chat_id: str | int) -> None:
        self._states.pop(str(chat_id), None)
