"""Сохранение наблюдаемых продаж в БД (история для графика в Mini App)."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.markets.base import Sale
from app.models import Sale as SaleRow


async def save_sales(s: AsyncSession, sales: Iterable[Sale]) -> int:
    items = {(x.market, x.event_id): x for x in sales}
    if not items:
        return 0
    existing = set(
        (
            await s.execute(
                select(SaleRow.market, SaleRow.event_id).where(
                    SaleRow.event_id.in_([k[1] for k in items])
                )
            )
        ).all()
    )
    added = 0
    for key, x in items.items():
        if key in existing:
            continue
        s.add(
            SaleRow(
                market=x.market,
                event_id=x.event_id,
                listing_id=x.listing_id,
                collection=x.collection,
                model=x.model,
                backdrop=x.backdrop,
                symbol=x.symbol,
                number=x.number,
                price_nano=x.price_nano,
                occurred_at=x.occurred_at,
            )
        )
        added += 1
    await s.flush()
    return added
