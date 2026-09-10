import asyncio
import re
from types import TracebackType
from typing import Any

import httpx

from fpx.classes.account.account import Account
from fpx.classes.runner.runner import Runner
from fpx.fsm import BaseStorage, MemoryStorage
from fpx.utils.errors import FpxAuthError

GKEY_PATTERN = re.compile(r"^[a-z0-9]{32}$")
GSEAL_PATTERN = re.compile(r"^v1\.[a-f0-9]{64}\.[a-f0-9]{32}\.\d+\.k\d+\.[a-f0-9]{64}$")


class FunPayTools:
    def __init__(
        self,
        gkey: str,
        gseal: str | None = None,
        storage: BaseStorage | None = None,
        proxy: str | httpx.Proxy | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if gseal or gseal is None:
            print(
                "ВАЖНО: С выхода релиза 0.8.0 аргумент gseal будет удалён, теперь он подставляется "
                "автоматически, просьба не передавать аргумент gseal во избежание проблем."
            )
        if not gkey:
            # TODO(#12): убрать ignore после аннотации fpx/utils/errors.py
            raise FpxAuthError("gkey и gseal не могут быть None.")  # type: ignore[no-untyped-call]
        if not GKEY_PATTERN.match(gkey):
            # TODO(#12): убрать ignore после аннотации fpx/utils/errors.py
            raise FpxAuthError("Неверный формат gkey, перепроверь его.")  # type: ignore[no-untyped-call]
        if gseal:
            if not GSEAL_PATTERN.match(gseal):
                # TODO(#12): убрать ignore после аннотации fpx/utils/errors.py
                raise FpxAuthError("Неверный формат gseal, перепроверь его.")  # type: ignore[no-untyped-call]
        self._cookies = {"golden_key": gkey, "locale": "ru"}
        if gseal:
            self._cookies["golden_seal"] = gseal
        self._headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept-Language": "ru-RU,ru;q=0.9",
        }
        mounts: dict[str, httpx.AsyncHTTPTransport] = {}
        if http_client and proxy:
            raise ValueError(
                "Нельзя передавать proxy и http_client вместе.В этом нет смысла, передавайте прокси внутри клиента"
            )
        if proxy:
            mounts = {
                "http://": httpx.AsyncHTTPTransport(proxy=proxy),
                "https://": httpx.AsyncHTTPTransport(proxy=proxy),
            }
        if http_client:
            self._client = http_client
            self._client.cookies.update(self._cookies)
            self._client.headers.update(self._headers)
        else:
            self._client = httpx.AsyncClient(
                http2=True,
                cookies=self._cookies,
                headers=self._headers,
                base_url="https://funpay.com",
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                timeout=httpx.Timeout(15.0),
                mounts=mounts,
            )
        # TODO(#20): Account(...) станет типизированным вызовом после аннотации fpx/classes/account/account.py
        self.account = Account(self._client)  # type: ignore[no-untyped-call]
        # TODO(#17): Runner(...) станет типизированным вызовом после аннотации fpx/classes/runner/runner.py
        self.runner = Runner(self.account)  # type: ignore[no-untyped-call]
        self.router = self.runner.router
        # TODO(#13): RequestEngine.runner сейчас объявлен без аннотации (фактически "None"),
        # из-за чего присвоение реального Runner формально не соответствует выведенному типу.
        self.account._request_engine.runner = self.runner  # type: ignore[assignment]
        # TODO(#13): MemoryStorage(...) станет типизированным вызовом после аннотации fpx/utils/storage
        self.storage = storage or MemoryStorage()  # type: ignore[no-untyped-call]
        self.runner.storage = self.storage
        self._refresh_task: asyncio.Task[Any] | None = None

        try:
            loop = asyncio.get_running_loop()
            # TODO(#20): refresh_cookies_cycle станет типизированным вызовом после аннотации fpx/classes/account
            self._refresh_task = loop.create_task(self.account.refresh_cookies_cycle())  # type: ignore[no-untyped-call]
        except RuntimeError:
            pass

    async def __aenter__(self) -> "FunPayTools":
        # TODO(#20): refresh_cookies_cycle станет типизированным вызовом после аннотации fpx/classes/account
        self._refresh_task = asyncio.create_task(self.account.refresh_cookies_cycle())  # type: ignore[no-untyped-call]
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.shutdown()

    async def shutdown(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        if hasattr(self, "runner") and self.runner.is_running:
            self.runner.is_running = False
        if self._client and not self._client.is_closed:
            await self._client.aclose()
