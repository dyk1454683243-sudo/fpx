import json
from typing import Any, cast

from .base import BaseStorage


class RedisStorage(BaseStorage):
    """
    Хранилище FSM на редис
    Внимание. при конкурентном доступе к одному chat_id
    возможна потеря данных (race condition).
    Для высоких нагрузок используйте Redis Lua-скрипты.
    """

    def __init__(self, url: str = "redis://localhost:6379", prefix: str = "fpx") -> None:
        try:
            # Redis - опциональная зависимость (extra "redis"), поэтому код ошибки
            # может отличаться в зависимости от того, установлен ли пакет:
            # import-not-found, если пакет не установлен вовсе, или import-untyped,
            # если установлен, но без разметки типов. Игнорируем оба случая.
            from redis.asyncio import Redis  # type: ignore
        except ImportError as e:
            raise ImportError("Redis не установлен. Установи: pip install fpx-engine[redis]") from e
        self._redis = Redis.from_url(url, decode_responses=True)
        self._prefix = prefix

    def _key(self, chat_id: str) -> str:
        return f"{self._prefix}:fsm:{chat_id}"

    async def set_state(self, chat_id: str | int, state: str | None) -> None:
        key = self._key(str(chat_id))
        data = await self.get_data(chat_id)
        await self._redis.set(key, json.dumps({"state": state, "data": data}))

    async def get_state(self, chat_id: str | int) -> str | None:
        raw = await self._redis.get(self._key(str(chat_id)))
        if not raw:
            return None
        return cast(str | None, json.loads(raw).get("state"))

    async def update_data(self, chat_id: str | int, **kwargs: Any) -> None:
        """Обновляет данные для чата.

        Warning: НЕ потокобезопасно. Если два хендлера
        одновременно пишут данные в один чат, одно из
        изменений может пропасть, не критично на слабых оборотах.
        """
        key = self._key(str(chat_id))
        current = await self.get_data(chat_id)
        current.update(kwargs)
        state = await self.get_state(chat_id)
        await self._redis.set(key, json.dumps({"state": state, "data": current}))

    async def get_data(self, chat_id: str | int) -> dict[str, Any]:
        raw = await self._redis.get(self._key(str(chat_id)))
        if not raw:
            return {}
        return cast(dict[str, Any], json.loads(raw).get("data", {}))

    async def clear_state(self, chat_id: str | int) -> None:
        await self._redis.delete(self._key(str(chat_id)))
