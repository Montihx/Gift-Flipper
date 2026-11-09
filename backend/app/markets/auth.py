"""initData Mini App маркетов через Telethon-сессию владельца (D-005, PLAN 2.2).

Источник схемы (из кода): aportalsmp `auth.py:30-44`, portalsmp `portalsapi.py:39-53`,
amrkt `client.py:217-230` — `messages.requestAppWebView(peer=@bot,
app=InputBotAppShortName(bot, short_name), platform)`; из URL берётся подстрока между
`tgWebAppData=` и `&tgWebAppVersion`, к ней один раз применяется `unquote`.

Для Tonnel бот и short_name в коде источников не найдены — задаются настройками
после проверки владельцем (HANDOFF §3). Токены живут только в памяти; перевыпуск —
по 401 (`invalidate`) или по запасному таймеру.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from urllib.parse import unquote

from app.markets.base import AuthRequired, Market
from app.timeutil import utcnow


@dataclass(frozen=True, slots=True)
class WebAppSpec:
    bot: str
    short_name: str
    platform: str


# Из кода источников; для Tonnel — нет данных (None), см. модульный docstring.
DEFAULT_SPECS: dict[Market, WebAppSpec | None] = {
    "portals": WebAppSpec(bot="portals", short_name="market", platform="desktop"),
    "mrkt": WebAppSpec(bot="mrkt", short_name="app", platform="android"),
    "tonnel": None,
}


def extract_init_data(webview_url: str) -> str:
    """`https://…#tgWebAppData=<urlencoded>&tgWebAppVersion=…` → сырой initData."""
    marker = "tgWebAppData="
    start = webview_url.find(marker)
    if start < 0:
        raise ValueError("в URL нет tgWebAppData")
    rest = webview_url[start + len(marker) :]
    end = rest.find("&tgWebAppVersion")
    raw = rest if end < 0 else rest[:end]
    if not raw:
        raise ValueError("пустой tgWebAppData")
    return unquote(raw)


class InitDataProvider(Protocol):
    async def init_data(self, market: Market) -> str: ...


class TelethonInitDataProvider:
    """Запрашивает WebView у бота маркета. Клиент Telethon передаётся уже подключённым."""

    def __init__(self, client: Any, specs: dict[Market, WebAppSpec | None] | None = None) -> None:
        self._client = client
        self._specs = dict(DEFAULT_SPECS) | dict(specs or {})

    async def init_data(self, market: Market) -> str:
        spec = self._specs.get(market)
        if spec is None:
            raise AuthRequired(f"{market}: не задан бот/short_name Mini App")
        from telethon.tl.functions.messages import RequestAppWebViewRequest
        from telethon.tl.types import InputBotAppShortName

        bot = await self._client.get_input_entity(spec.bot)
        result = await self._client(
            RequestAppWebViewRequest(
                peer=bot,
                app=InputBotAppShortName(bot_id=bot, short_name=spec.short_name),
                platform=spec.platform,
            )
        )
        return extract_init_data(result.url)


@dataclass
class _Cached:
    value: str
    obtained_at: datetime


class TokenCache:
    """Кэш строк авторизации по маркету. Значения не логируются."""

    def __init__(
        self,
        fetch: Callable[[Market], Awaitable[str]],
        max_age: timedelta = timedelta(hours=12),
        now: Callable[[], datetime] = utcnow,
    ) -> None:
        self._fetch = fetch
        self._max_age = max_age
        self._now = now
        self._items: dict[Market, _Cached] = {}
        self._locks: dict[Market, asyncio.Lock] = {}

    async def get(self, market: Market) -> str:
        lock = self._locks.setdefault(market, asyncio.Lock())
        async with lock:
            item = self._items.get(market)
            if item is None or self._now() - item.obtained_at >= self._max_age:
                item = _Cached(await self._fetch(market), self._now())
                self._items[market] = item
            return item.value

    def invalidate(self, market: Market) -> None:
        self._items.pop(market, None)
