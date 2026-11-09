"""Tonnel — клиент только для чтения (PLAN 2.5, D-014).

Источники (из кода): topcvetok @ 05f658a (D-015) — `pageGifts` без авторизации, поток событий
`wss://gifts.coffin.meme/api/marketplace/ws` и догонка `GET …/marketplace/events`, форматы событий
из фикстур; bleach-hub/tonnelmp @ 68064f7 — `filterStats`, фильтры `$regex`. Код tonnelmp
не менялся с 2025-06 — каждый путь проверить на живом ответе (решение владельца 2026-11-09).

`saleHistory` не реализован: формат ответа в коде источников не найден. Продажи берутся из
событий `sale.completed`.
"""

from __future__ import annotations

import json
import logging
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.markets.base import (
    CollectionFloor,
    Listing,
    Market,
    Sale,
    SchemaError,
    SearchQuery,
    rarity_permille,
    strip_rarity,
)
from app.markets.http import MarketHttp, Route
from app.money import ton_to_nano
from app.timeutil import parse_iso

log = logging.getLogger(__name__)

BASE_URL = "https://gifts2.tonnel.network/api/"
EVENTS_URL = "https://gifts.coffin.meme/api/marketplace/events"
EVENTS_WS_URL = "wss://gifts.coffin.meme/api/marketplace/ws"
HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Origin": "https://market.tonnel.network",
    "Referer": "https://market.tonnel.network/",
}
READ_ROUTES = [
    Route("POST", r"/api/pageGifts"),
    Route("POST", r"/api/filterStats"),
    Route("GET", r"/api/marketplace/events"),
]
MAX_LIMIT = 30
SORTS = {
    "latest": {"message_post_time": -1, "gift_id": -1},
    "price_asc": {"price": 1, "gift_id": -1},
}
ACTIVE_FILTER = {
    "price": {"$exists": True},
    "refunded": {"$ne": True},
    "buyer": {"$exists": False},
    "export_at": {"$exists": True},
    "asset": "TON",
}
_REGEX_META = set(r"\^$.|?*+()[]{}")


def _regex_prefix(value: str) -> dict[str, str]:
    """Атрибут без редкости: `{"$regex": "^Name \\("}` (из кода tonnelmp)."""
    escaped = "".join("\\" + ch if ch in _REGEX_META else ch for ch in value)
    return {"$regex": f"^{escaped} \\("}


def _price(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal, str)):
        raise SchemaError(f"tonnel: цена неожиданного типа {type(value).__name__}")
    return ton_to_nano(value)


def is_active(gift: dict[str, Any]) -> bool:
    """Активный лот (из кода topcvetok tonnel_watch.py:260-271)."""
    return (
        gift.get("status", "forsale") == "forsale"
        and gift.get("asset", "TON") == "TON"
        and not gift.get("auction")
        and not gift.get("dutchAuctionData")
        and not gift.get("premarketData")
        and gift.get("underLoan") is not True
    )


def parse_gift(gift: dict[str, Any], *, price: Any = None) -> Listing:
    try:
        gift_id = int(gift["gift_id"])
        collection = str(gift.get("name") or gift["gift_name"])
        nano = _price(gift["price"] if price is None else price)
    except (KeyError, TypeError, ValueError) as exc:
        raise SchemaError(f"tonnel: плохой подарок: {exc}") from exc
    number = gift.get("gift_num")
    return Listing(
        market="tonnel",
        listing_id=str(gift_id),
        collection=collection,
        model=strip_rarity(gift.get("model")),
        backdrop=strip_rarity(gift.get("backdrop")),
        symbol=strip_rarity(gift.get("symbol")),
        number=int(number) if number is not None else None,
        price_nano=nano,
        url=f"https://t.me/tonnel_network_bot/gift?startapp={gift_id}",
        is_bundle=gift_id < 0,
        is_premarket=bool(gift.get("premarketData")),
        is_auction=bool(gift.get("auction") or gift.get("dutchAuctionData")),
        model_rarity_pm=rarity_permille(gift.get("model")),
        backdrop_rarity_pm=rarity_permille(gift.get("backdrop")),
        symbol_rarity_pm=rarity_permille(gift.get("symbol")),
    )


@dataclass(frozen=True, slots=True)
class ListingEvent:
    event_id: str
    kind: str  # created | price_changed
    listing: Listing
    occurred_at: datetime | None


def _event_time(event: dict[str, Any]) -> datetime | None:
    try:
        return parse_iso(str(event["occurredAt"])) if event.get("occurredAt") else None
    except ValueError:
        return None


def parse_event(event: Any) -> ListingEvent | Sale | None:
    """Событие потока → листинг/продажа; прочее (премаркет, аукционы, не TON) → None.

    Форматы — из фикстур topcvetok test_tonnel_watch.py.
    """
    if not isinstance(event, dict) or not event.get("eventId"):
        return None
    kind = event.get("type")
    data = event.get("data")
    if not isinstance(data, dict) or data.get("asset") != "TON":
        return None
    gift = data.get("gift")
    if not isinstance(gift, dict) or gift.get("gift_id") is None:
        return None
    if kind == "sale.completed":
        occurred = _event_time(event)
        if occurred is None:
            return None
        g = parse_gift(gift, price=data.get("price"))
        return Sale(
            "tonnel",
            str(event["eventId"]),
            g.collection,
            g.model,
            g.backdrop,
            g.symbol,
            g.number,
            g.price_nano,
            occurred,
            listing_id=g.listing_id,
        )
    if kind == "listing.created" and data.get("sale_type") == "FIXED":
        return ListingEvent(
            str(event["eventId"]),
            "created",
            parse_gift(gift, price=data.get("price")),
            _event_time(event),
        )
    if kind == "listing.price_changed":
        return ListingEvent(
            str(event["eventId"]),
            "price_changed",
            parse_gift(gift, price=data.get("price")),
            _event_time(event),
        )
    return None


class TonnelClient:
    market: Market = "tonnel"

    def __init__(
        self,
        http: MarketHttp,
        init_data: Callable[[], Awaitable[str]] | None = None,
        sales_buffer: int = 500,
    ) -> None:
        self._http = http
        self._init_data = init_data
        self._sales: deque[Sale] = deque(maxlen=sales_buffer)

    async def search(self, query: SearchQuery) -> list[Listing]:
        flt: dict[str, Any] = dict(ACTIVE_FILTER)
        if query.collection:
            flt["gift_name"] = query.collection
        if query.model:
            flt["model"] = _regex_prefix(query.model)
        if query.backdrop:
            flt["backdrop"] = _regex_prefix(query.backdrop)
        if query.symbol:
            flt["symbol"] = _regex_prefix(query.symbol)
        body = {
            "page": 1,
            "limit": min(query.limit, MAX_LIMIT),
            "sort": json.dumps(SORTS[query.sort], separators=(",", ":")),
            "filter": json.dumps(flt, separators=(",", ":")),
            "price_range": None,
            "user_auth": "",
        }
        data = await self._http.post_json("pageGifts", body)
        if not isinstance(data, list):
            raise SchemaError("tonnel: pageGifts вернул не список")
        out = []
        for g in data:
            if isinstance(g, dict) and is_active(g):
                listing = parse_gift(g)
                if not listing.is_bundle:
                    out.append(listing)
        return out

    async def floors(self) -> list[CollectionFloor]:
        """Флоры по модели из `filterStats` (требует initData). Без авторизации — пусто."""
        if self._init_data is None:
            log.info("tonnel: filterStats пропущен — нет initData")
            return []
        data = await self._http.post_json("filterStats", {"authData": await self._init_data()})
        if not isinstance(data, dict) or data.get("status") != "success":
            raise SchemaError("tonnel: filterStats status != success")
        out = []
        for key, value in (data.get("data") or {}).items():
            if not isinstance(value, dict) or value.get("floorPrice") in (None, 0):
                continue
            collection, _, model = str(key).partition("_")
            out.append(
                CollectionFloor(
                    "tonnel",
                    collection.strip(),
                    _price(value["floorPrice"]),
                    model=strip_rarity(model) if model else None,
                    count=value.get("howMany"),
                )
            )
        return out

    def remember_sale(self, sale: Sale) -> None:
        self._sales.appendleft(sale)

    async def recent_sales(self, limit: int = 20) -> list[Sale]:
        """Продажи из потока событий (накапливаются `remember_sale`)."""
        return list(self._sales)[:limit]

    async def get_listing(self, listing_id: str) -> Listing | None:
        """Подтверждённого маршрута карточки нет (tonnelmp `giftData` ничего не возвращает);
        статус лота узнаём из событий `sale.completed`. Всегда None."""
        return None

    async def replay_events(self, after: str, limit: int = 100) -> tuple[list[Any], str | None]:
        """Догонка после обрыва WS: `GET …/events?after=<eventId>&limit=100` (topcvetok)."""
        data = await self._http.get_json(EVENTS_URL, params={"after": after, "limit": limit})
        events = data.get("events") if isinstance(data, dict) else None
        if not isinstance(events, list):
            raise SchemaError("tonnel: events без ключа events")
        nxt = data.get("nextAfter")
        return events, nxt if isinstance(nxt, str) else None

    async def aclose(self) -> None:
        await self._http.aclose()


async def stream_events(
    connect: Callable[[], Awaitable[Any]],
) -> AsyncIterator[Any]:
    """Сырые события из WebSocket. `connect` возвращает объект с `recv()`/`close()`.

    Подключение без авторизации и без подписки (из кода topcvetok). Переподключение
    и догонка — в engine.
    """
    ws = await connect()
    try:
        while True:
            raw = await ws.recv()
            payload = raw[0] if isinstance(raw, tuple) else raw
            try:
                yield json.loads(payload, parse_float=Decimal)
            except ValueError:
                log.warning("tonnel: не JSON в потоке событий")
    finally:
        await ws.close()
