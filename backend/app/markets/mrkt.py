"""MRKT — клиент только для чтения (PLAN 2.4).

Источники (из кода): TheBrainAir/amrkt @ 2a4dbf5 — пути, заголовки, модель подарка, nanoTON;
boostNT/MRKT-API (README) — `/auth`, `/gifts/saling`, `count` ≤ 20, `Referer` против 429;
topcvetok @ b0e81f2^ (D-015) — тело `/feed` с `type: ["Sale"]`. Живыми ответами не проверено.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.markets.base import CollectionFloor, Listing, Market, Sale, SchemaError, SearchQuery
from app.markets.http import HttpError, MarketHttp, Route
from app.timeutil import parse_iso, utcnow

BASE_URL = "https://api.tgmrkt.io/api/v1/"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://cdn.tgmrkt.io",
    "Referer": "https://cdn.tgmrkt.io/",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
}
_ID = r"[0-9a-fA-F-]{8,64}"
READ_ROUTES = [
    Route("POST", r"/api/v1/auth"),
    Route("POST", r"/api/v1/gifts/saling"),
    Route("GET", r"/api/v1/gifts/collections"),
    Route("POST", r"/api/v1/feed"),
    Route("GET", rf"/api/v1/gifts/gift/{_ID}"),
]
MAX_COUNT = 20  # boostNT README; amrkt-пример использует 50 — не подтверждено


def _nano(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise SchemaError(f"mrkt: цена не целое nanoTON: {type(value).__name__}")
    if isinstance(value, Decimal):
        if value != value.to_integral_value():
            raise SchemaError("mrkt: дробный nanoTON")
        value = int(value)
    if value <= 0:
        raise SchemaError("mrkt: цена ≤ 0")
    return value


def _time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return parse_iso(str(value))
    except ValueError:
        return None


def parse_gift(gift: dict[str, Any]) -> Listing:
    try:
        gid = str(gift["id"])
        collection = str(gift["collectionName"])
        price = _nano(gift["salePrice"])
    except KeyError as exc:
        raise SchemaError(f"mrkt: нет поля {exc}") from exc
    number = gift.get("number")
    resale = _time(gift.get("nextResaleDate"))
    return Listing(
        market="mrkt",
        listing_id=gid,
        collection=collection,
        model=gift.get("modelName"),
        backdrop=gift.get("backdropName"),
        symbol=gift.get("symbolName"),
        number=int(number) if number is not None else None,
        price_nano=price,
        url=f"https://t.me/mrkt/app?startapp=gift{gid.replace('-', '')}",
        is_premarket=gift.get("premarketStatus") not in (None, "", "None"),
        is_auction=bool(gift.get("isOnAuction")),
        locked_until=resale if resale and resale > utcnow() else None,
    )


class MrktClient:
    market: Market = "mrkt"

    def __init__(self, http: MarketHttp, init_data: Callable[[], Awaitable[str]]) -> None:
        self._http = http
        self._init_data = init_data
        self._token: str | None = None

    async def _login(self) -> str:
        data = await self._http.post_json("auth", {"data": await self._init_data()})
        token = data.get("token") if isinstance(data, dict) else None
        if not isinstance(token, str) or not token:
            raise SchemaError("mrkt: в ответе /auth нет token")
        self._token = token
        return token

    async def _call(self, method: str, path: str, body: Any = None) -> Any:
        for attempt in (0, 1):
            token = self._token or await self._login()
            headers = {"Authorization": token, "Cookie": f"access_token={token}"}
            try:
                resp = await self._http.request(method, path, json_body=body, headers=headers)
                return resp.json()
            except HttpError as exc:
                if exc.status == 401 and attempt == 0:
                    self._token = None  # перевыпуск по 401 (D-005)
                    continue
                raise
        raise AssertionError("unreachable")  # pragma: no cover

    async def search(self, query: SearchQuery) -> list[Listing]:
        body = {
            "collectionNames": [query.collection] if query.collection else [],
            "modelNames": [query.model] if query.model else [],
            "backdropNames": [query.backdrop] if query.backdrop else [],
            "symbolNames": [query.symbol] if query.symbol else [],
            "ordering": "Price" if query.sort == "price_asc" else None,
            "lowToHigh": query.sort == "price_asc",
            "minPrice": query.min_price_nano,
            "maxPrice": query.max_price_nano,
            "mintable": None,
            "number": None,
            "count": min(query.limit, MAX_COUNT),
            "cursor": "",
            "query": None,
            "promotedFirst": False,
        }
        data = await self._call("POST", "gifts/saling", body)
        gifts = data.get("gifts") if isinstance(data, dict) else None
        if not isinstance(gifts, list):
            raise SchemaError("mrkt: нет ключа gifts")
        return [
            parse_gift(g)
            for g in gifts
            if isinstance(g, dict) and g.get("isOnSale", True) and not g.get("isMine")
        ]

    async def floors(self) -> list[CollectionFloor]:
        data = await self._call("GET", "gifts/collections")
        if not isinstance(data, list):
            raise SchemaError("mrkt: /gifts/collections не список")
        out = []
        for c in data:
            if not isinstance(c, dict) or c.get("isHidden"):
                continue
            floor = c.get("floorPriceNanoTons")
            if floor in (None, 0) or not c.get("name"):
                continue
            out.append(CollectionFloor("mrkt", str(c["name"]), _nano(floor)))
        return out

    async def recent_sales(self, limit: int = 20) -> list[Sale]:
        body = {
            "count": min(limit, MAX_COUNT),
            "cursor": "",
            "collectionNames": [],
            "modelNames": [],
            "backdropNames": [],
            "number": None,
            "type": ["Sale"],
            "minPrice": None,
            "maxPrice": None,
            "ordering": "Latest",
            "lowToHigh": False,
            "query": None,
        }
        data = await self._call("POST", "feed", body)
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            raise SchemaError("mrkt: нет ключа items")
        out = []
        for it in items:
            if not isinstance(it, dict) or str(it.get("type", "")).casefold() != "sale":
                continue
            gift = it.get("gift")
            occurred = _time(it.get("date"))
            if not isinstance(gift, dict) or occurred is None or not it.get("id"):
                continue
            g = parse_gift({**gift, "salePrice": it.get("amount", gift.get("salePrice"))})
            out.append(
                Sale(
                    "mrkt",
                    str(it["id"]),
                    g.collection,
                    g.model,
                    g.backdrop,
                    g.symbol,
                    g.number,
                    g.price_nano,
                    occurred,
                    listing_id=g.listing_id,
                )
            )
        return out

    async def get_listing(self, listing_id: str) -> Listing | None:
        try:
            data = await self._call("GET", f"gifts/gift/{listing_id}")
        except HttpError as exc:
            if exc.status == 404:
                return None
            raise
        if not isinstance(data, dict) or not data.get("isOnSale"):
            return None
        return parse_gift(data)

    async def aclose(self) -> None:
        await self._http.aclose()
