"""Portals — клиент только для чтения (PLAN 2.3).

Источники (из кода): bleach-hub/aportalsmp @ d1daafd (D-013) — пути, параметры, поля;
topcvetok/telegram-gift-watch @ 05f658a (D-015) — публичные маршруты без авторизации,
лимит ≥1,2 с между запросами. Живыми ответами не проверено (MARKETS.md §1).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.markets.base import (
    CollectionFloor,
    Listing,
    Market,
    MarketError,
    Sale,
    SchemaError,
    SearchQuery,
)
from app.markets.http import HttpError, MarketHttp, Route
from app.money import ton_to_nano
from app.timeutil import parse_iso, utcnow

BASE_URL = "https://portal-market.com/api/"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://portal-market.com",
    "Referer": "https://portal-market.com/",
}
_UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
READ_ROUTES = [
    Route("GET", r"/api/nfts/search"),
    Route("GET", rf"/api/nfts/{_UUID}"),
    Route("GET", r"/api/collections"),
    Route("GET", r"/api/collections/floors"),
    Route("GET", r"/api/collections/filters"),
    Route("GET", r"/api/market/actions/"),
]
SORTS = {"latest": "listed_at desc", "price_asc": "price asc"}


def _price(value: Any) -> int:
    if not isinstance(value, (str, int, Decimal)):
        raise SchemaError(f"portals: цена неожиданного типа {type(value).__name__}")
    return ton_to_nano(value)


def _attr(gift: dict[str, Any], kind: str, field: str = "value") -> Any:
    for attr in gift.get("attributes") or []:
        if isinstance(attr, dict) and attr.get("type") == kind:
            return attr.get(field)
    return None


def _pm(gift: dict[str, Any], kind: str) -> int | None:
    """`rarity_per_mille` (из кода aportalsmp Objects.py)."""
    v = _attr(gift, kind, "rarity_per_mille")
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return parse_iso(str(value))
    except ValueError:
        return None


def parse_gift(gift: dict[str, Any]) -> Listing:
    try:
        listing_id = str(gift["id"])
        collection = str(gift["name"])
        price = _price(gift["price"])
    except KeyError as exc:
        raise SchemaError(f"portals: нет поля {exc}") from exc
    number = gift.get("external_collection_number")
    unlocks = _time(gift.get("unlocks_at"))
    return Listing(
        market="portals",
        listing_id=listing_id,
        collection=collection,
        model=_attr(gift, "model"),
        backdrop=_attr(gift, "backdrop"),
        symbol=_attr(gift, "symbol"),
        number=int(number) if number is not None else None,
        price_nano=price,
        listed_at=_time(gift.get("listed_at")),
        url=f"https://t.me/portals/market?startapp=gift_{listing_id}",
        locked_until=unlocks if unlocks and unlocks > utcnow() else None,
        raw_id=gift.get("tg_id"),
        model_rarity_pm=_pm(gift, "model"),
        backdrop_rarity_pm=_pm(gift, "backdrop"),
        symbol_rarity_pm=_pm(gift, "symbol"),
    )


class PortalsClient:
    market: Market = "portals"

    def __init__(
        self,
        http: MarketHttp,
        auth: Callable[[], Awaitable[str]] | None = None,
    ) -> None:
        self._http = http
        self._auth = auth
        self._collection_ids: dict[str, str] = {}

    async def _headers(self, required: bool = False) -> dict[str, str]:
        if self._auth is None:
            if required:
                raise MarketError("portals: маршрут требует initData")
            return {}
        return {"Authorization": f"tma {await self._auth()}"}

    async def collections(self, limit: int = 100) -> list[dict[str, Any]]:
        data = await self._http.get_json(
            "collections", params={"limit": limit}, headers=await self._headers()
        )
        items = data.get("collections") if isinstance(data, dict) else None
        if not isinstance(items, list):
            raise SchemaError("portals: нет ключа collections")
        for c in items:
            if isinstance(c, dict) and c.get("name") and c.get("id"):
                self._collection_ids[str(c["name"])] = str(c["id"])
        return items

    async def _collection_id(self, name: str) -> str | None:
        if name not in self._collection_ids:
            await self.collections()
        return self._collection_ids.get(name)

    async def search(self, query: SearchQuery) -> list[Listing]:
        params: dict[str, Any] = {
            "offset": 0,
            "limit": min(query.limit, 20),
            "sort_by": SORTS[query.sort],
            "status": "listed",
            "exclude_bundled": "true",
            "premarket_status": "without_premarket",
        }
        if query.collection:
            cid = await self._collection_id(query.collection)
            if cid is None:
                raise MarketError(f"portals: коллекция не найдена: {query.collection}")
            params["collection_ids"] = cid
        if query.model:
            params["filter_by_models"] = query.model
        if query.backdrop:
            params["filter_by_backdrops"] = query.backdrop
        if query.symbol:
            params["filter_by_symbols"] = query.symbol
        data = await self._http.get_json(
            "nfts/search", params=params, headers=await self._headers()
        )
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list):
            raise SchemaError("portals: нет ключа results")
        out = []
        for g in results:
            if isinstance(g, dict) and g.get("status", "listed") == "listed":
                out.append(parse_gift(g))
        return out

    async def floors(self) -> list[CollectionFloor]:
        out = []
        for c in await self.collections():
            if not isinstance(c, dict) or c.get("floor_price") in (None, "", "0"):
                continue
            out.append(CollectionFloor("portals", str(c["name"]), _price(c["floor_price"])))
        return out

    async def recent_sales(self, limit: int = 20) -> list[Sale]:
        data = await self._http.get_json(
            "market/actions/",
            params={
                "offset": 0,
                "limit": min(limit, 20),
                "sort_by": SORTS["latest"],
                "action_types": "buy",
            },
            headers=await self._headers(required=True),
        )
        actions = data.get("actions") if isinstance(data, dict) else None
        if not isinstance(actions, list):
            raise SchemaError("portals: нет ключа actions")
        out = []
        for a in actions:
            if (
                not isinstance(a, dict)
                or a.get("type") != "buy"
                or not isinstance(a.get("nft"), dict)
            ):
                continue
            gift = parse_gift({**a["nft"], "price": a.get("amount", a["nft"].get("price"))})
            occurred = _time(a.get("created_at"))
            if occurred is None:
                continue
            out.append(
                Sale(
                    market="portals",
                    event_id=f"{gift.listing_id}:{a.get('created_at')}",
                    collection=gift.collection,
                    model=gift.model,
                    backdrop=gift.backdrop,
                    symbol=gift.symbol,
                    number=gift.number,
                    price_nano=gift.price_nano,
                    occurred_at=occurred,
                    listing_id=gift.listing_id,
                )
            )
        return out

    async def get_listing(self, listing_id: str) -> Listing | None:
        try:
            data = await self._http.get_json(f"nfts/{listing_id}", headers=await self._headers())
        except HttpError as exc:
            if exc.status == 404:
                return None
            raise
        if not isinstance(data, dict) or data.get("status") != "listed":
            return None
        return parse_gift(data)

    async def aclose(self) -> None:
        await self._http.aclose()
