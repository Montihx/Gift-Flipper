"""Фабрики тестовых объектов. Цены задаются в TON (int/str) и переводятся в nanoTON."""

from __future__ import annotations

from datetime import UTC, datetime

from app.markets.base import Listing, Sale
from app.money import ton_to_nano

NOW = datetime(2026, 11, 9, 12, tzinfo=UTC)


def listing(
    listing_id: str = "a",
    price: int | str = 10,
    market: str = "portals",
    collection: str = "Evil Eye",
    model: str | None = "Watcher",
    backdrop: str | None = "Onyx Black",
    symbol: str | None = "Moon",
    number: int | None = 42,
    **kw,
) -> Listing:
    return Listing(
        market=market,  # type: ignore[arg-type]
        listing_id=listing_id,
        collection=collection,
        model=model,
        backdrop=backdrop,
        symbol=symbol,
        number=number,
        price_nano=ton_to_nano(price),
        **kw,
    )


def sale(
    event_id: str = "s1",
    price: int | str = 10,
    market: str = "tonnel",
    collection: str = "Evil Eye",
    model: str | None = "Watcher",
    backdrop: str | None = "Onyx Black",
    occurred_at: datetime = NOW,
    **kw,
) -> Sale:
    return Sale(
        market=market,  # type: ignore[arg-type]
        event_id=event_id,
        collection=collection,
        model=model,
        backdrop=backdrop,
        symbol=kw.pop("symbol", None),
        number=kw.pop("number", None),
        price_nano=ton_to_nano(price),
        occurred_at=occurred_at,
        **kw,
    )
