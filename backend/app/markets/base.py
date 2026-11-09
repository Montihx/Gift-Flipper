"""Общий интерфейс клиентов маркетов и нормализованные модели (PLAN 2.1).

Все цены — nanoTON (int). Время — UTC с tz. Клиенты только читают: пути покупки,
листинга и вывода сюда не входят и запрещены на уровне HTTP (`http.ReadOnlyGuard`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

Market = Literal["portals", "mrkt", "tonnel"]
MARKETS: tuple[Market, ...] = ("portals", "mrkt", "tonnel")

_RARITY_SUFFIX = re.compile(r"\s*\(\s*[\d.,]+\s*%\s*\)\s*$")


def strip_rarity(value: str | None) -> str | None:
    """Tonnel отдаёт атрибуты как `"Black (1%)"` (из кода topcvetok, tonnelmp)."""
    if value is None:
        return None
    cleaned = _RARITY_SUFFIX.sub("", str(value)).strip()
    return cleaned or None


@dataclass(frozen=True, slots=True)
class Listing:
    market: Market
    listing_id: str
    collection: str
    model: str | None
    backdrop: str | None
    symbol: str | None
    number: int | None
    price_nano: int
    listed_at: datetime | None = None
    url: str | None = None
    # Признаки «ловушек» (SUMMARY.md §2): не покупаем и не считаем сопоставимыми.
    is_bundle: bool = False
    is_premarket: bool = False
    is_auction: bool = False
    locked_until: datetime | None = None
    # Цена с комиссией покупателя заполняется в pricing/ (Этап 3), не клиентом.
    all_in_nano: int | None = None
    raw_id: str | None = None  # gift_id/tg_id маркета, если отличается от listing_id

    @property
    def key(self) -> str:
        """Ключ дедупа `market:id:price` (PLAN 4.3)."""
        return f"{self.market}:{self.listing_id}:{self.price_nano}"


@dataclass(frozen=True, slots=True)
class Sale:
    market: Market
    event_id: str
    collection: str
    model: str | None
    backdrop: str | None
    symbol: str | None
    number: int | None
    price_nano: int
    occurred_at: datetime
    listing_id: str | None = None


@dataclass(frozen=True, slots=True)
class CollectionFloor:
    market: Market
    collection: str
    floor_nano: int
    model: str | None = None
    backdrop: str | None = None
    count: int | None = None  # сколько объявлений за флором, если маркет сообщает


@dataclass(frozen=True, slots=True)
class SearchQuery:
    collection: str | None = None
    model: str | None = None
    backdrop: str | None = None
    symbol: str | None = None
    sort: Literal["price_asc", "latest"] = "latest"
    limit: int = 20
    min_price_nano: int | None = None
    max_price_nano: int | None = None
    extra: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class MarketClient(Protocol):
    market: Market

    async def search(self, query: SearchQuery) -> list[Listing]: ...

    async def floors(self) -> list[CollectionFloor]: ...

    async def recent_sales(self, limit: int = 20) -> list[Sale]: ...

    async def get_listing(self, listing_id: str) -> Listing | None: ...

    async def aclose(self) -> None: ...


class MarketError(RuntimeError):
    """Ошибка маркета, после которой цикл продолжает работу с другими маркетами."""


class SchemaError(MarketError):
    """Ответ не соответствует ожидаемой схеме — маркет мог поменять API."""


class AuthRequired(MarketError):
    """Маршрут требует initData/токен, а провайдер не настроен."""
