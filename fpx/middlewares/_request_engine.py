import asyncio
from typing import TYPE_CHECKING, Any

import httpx

from fpx.utils import errors as fpx_err

if TYPE_CHECKING:
    from fpx.classes.runner.runner import Runner


class RequestEngine:
    def __init__(self, account: Any, client: httpx.AsyncClient) -> None:
        # account: Account (см. fpx/classes/account/account.py). Оставлен как Any,
        # так как сам класс Account ещё не аннотирован (отдельная задача #20).
        self._account = account
        self._client = client
        self.runner: "Runner | None" = None

    async def execute(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        attempts = 3
        backoff = 1.5  # множитель времени ожидания
        if method.upper() in ("POST", "PUT", "DELETE"):
            if "data" not in kwargs:
                kwargs["data"] = {}
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            if self._account.data._csrf_token is None:
                await self._account.profile.get_user_data()
            if "csrf_token" not in kwargs["data"]:
                kwargs["data"]["csrf_token"] = self._account.data._csrf_token
            if "X-Cp-Csrf-Token" not in kwargs["headers"]:
                kwargs["headers"]["X-Cp-Csrf-Token"] = self._account.data._csrf_token
        for attempt in range(attempts):
            try:
                response = await self._client.request(method, url, **kwargs)
                # флуд контрль
                if response.status_code == 429:
                    if attempt == attempts - 1:
                        raise fpx_err.FpxRequestError(message=f"Превышено кол-во попыток запроса (Flood/429) к {url}")
                    try:
                        sleep_time = int(response.headers.get("Retry-After", 5))
                    except (ValueError, TypeError):
                        sleep_time = 5
                    if self.runner:
                        for handler in self.runner.router._handlers["flood"]:
                            asyncio.create_task(handler(sleep_time))
                    await asyncio.sleep(sleep_time)
                    continue
                # если чето сервер не ответил
                if response.status_code in (502, 503, 504):
                    sleep_time = backoff ** float(attempt)
                    await asyncio.sleep(sleep_time)
                    continue
                if response.url == "https://funpay.com/account/login":
                    raise fpx_err.FpxAuthError("Неверный gkey, обнови свои куки.")
                return response
            except httpx.ReadTimeout as e:
                if method.upper() == "GET":
                    if attempt == attempts - 1:
                        raise e
                    await asyncio.sleep(backoff**attempt)
                else:
                    raise fpx_err.FpxRequestError(
                        message=f"POST запрос упал по таймауту ответаВозможно действие выполнилось: {e}"
                    )
            except (httpx.ConnectTimeout, httpx.ConnectError) as e:
                if attempt == attempts - 1:
                    raise e
                await asyncio.sleep(backoff**attempt)
        raise fpx_err.FpxRequestError(message=f"Превышено количество попыток запроса к {url}")
