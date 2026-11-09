"""Живые клиенты (только чтение). Запускается на ПК владельца (D-016)."""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from itertools import count
from pathlib import Path
from typing import Any

from app.markets.auth import TelethonInitDataProvider, TokenCache
from app.markets.base import MARKETS, Market, MarketClient
from app.markets.factory import make_client
from app.markets.http import CurlTransport, Response, Transport
from app.security import ensure_private_dir, is_private_file, mask_secrets
from app.settings import Settings

log = logging.getLogger(__name__)


class RecordingTransport:
    """Сохраняет ответы для фикстур. Тела запросов не пишутся; ответы маскируются."""

    def __init__(self, inner: Transport, market: str, root: Path) -> None:
        self._inner = inner
        self._dir = ensure_private_dir(root / market)
        self._seq = count(1)

    async def request(self, method, url, *, params, json_body, headers, timeout) -> Response:
        resp = await self._inner.request(
            method, url, params=params, json_body=json_body, headers=headers, timeout=timeout
        )
        path = (
            self._dir / f"{next(self._seq):03d}_{method}_{url.split('/')[-1][:40] or 'root'}.json"
        )
        record: dict[str, Any] = {
            "_source": "live",
            "method": method,
            "url": url,
            "params": params,
            "status": resp.status,
            "body": mask_secrets(resp.body.decode("utf-8", "replace")),
        }
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str), "utf-8")
        path.chmod(0o600)
        return resp

    async def aclose(self) -> None:
        await self._inner.aclose()


async def live_clients(
    settings: Settings, record_dir: Path | None = None
) -> tuple[list[MarketClient], Callable[[], Awaitable[None]]]:
    from telethon import TelegramClient

    if settings.tg_api_id is None or settings.tg_api_hash is None:
        raise SystemExit("нет TG_API_ID/TG_API_HASH в .env")
    session = settings.tg_session_path
    if not session.exists():
        raise SystemExit(f"нет сессии {session}; войдите: python -m app.tools.login")
    if not is_private_file(session):
        raise SystemExit(f"права на {session} шире 600: chmod 600")
    tg = TelegramClient(
        str(session.with_suffix("")), settings.tg_api_id, settings.tg_api_hash.get_secret_value()
    )
    await tg.connect()
    if not await tg.is_user_authorized():
        await tg.disconnect()
        raise SystemExit("сессия не авторизована: python -m app.tools.login")
    provider = TelethonInitDataProvider(tg)
    cache = TokenCache(provider.init_data)

    def init_for(market: Market) -> Callable[[], Awaitable[str]]:
        return lambda: cache.get(market)

    clients: list[MarketClient] = []
    for market in MARKETS:
        transport: Transport = CurlTransport()
        if record_dir is not None:
            transport = RecordingTransport(transport, market, record_dir)
        # Tonnel: бот Mini App не задан → без initData (публичный pageGifts).
        init = None if market == "tonnel" else init_for(market)
        clients.append(make_client(market, settings, init_data=init, transport=transport))

    async def close() -> None:
        await tg.disconnect()

    return clients, close
