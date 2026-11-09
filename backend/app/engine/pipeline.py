"""Цикл: листинги → книги → оценка → пресеты → уведомления (watch). Продажи → «ПРОДАНО».

Покупок нет и вызова исполнения нет: режим всегда watch (D-003, Этап 7 не разрешён).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.markets.base import Listing, Market, MarketClient, MarketError, Sale, SearchQuery
from app.pricing.deal import Deal, evaluate
from app.rules.match import PresetRule, match_presets

log = logging.getLogger(__name__)


class Notify(Protocol):
    async def notify(self, chat_id: int, deal: Deal, match: Any) -> Any: ...

    async def mark_sold(
        self, market: str, listing_id: str, price_nano: int | None = None
    ) -> int: ...


@dataclass
class CycleResult:
    listings: int = 0
    evaluated: int = 0
    notified: int = 0
    sold_marked: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class Pipeline:
    clients: Sequence[MarketClient]
    notifier: Notify
    owner_chat_id: int
    book_limit: int = 30
    seen: set[str] = field(default_factory=set)  # ключи market:id:price
    sales: list[Sale] = field(default_factory=list)

    async def _safe(self, coro, market: str, errors: list[str]):
        try:
            return await coro
        except MarketError as exc:
            errors.append(f"{market}: {exc}")
            log.warning("%s: %s", market, exc)
            return None

    async def run_cycle(
        self, rules: Sequence[PresetRule], now: datetime, latest_limit: int = 20
    ) -> CycleResult:
        res = CycleResult()
        fresh: list[Listing] = []
        for c in self.clients:
            items = (
                await self._safe(
                    c.search(SearchQuery(sort="latest", limit=latest_limit)), c.market, res.errors
                )
                or []
            )
            res.listings += len(items)
            fresh.extend(x for x in items if x.key not in self.seen)
            sales = await self._safe(c.recent_sales(), c.market, res.errors) or []
            known = {(s.market, s.event_id) for s in self.sales}
            for s in sales:
                if (s.market, s.event_id) in known:
                    continue
                self.sales.append(s)
                if s.listing_id:
                    res.sold_marked += (
                        await self.notifier.mark_sold(s.market, s.listing_id, s.price_nano) or 0
                    )
        if not fresh or not any(r.enabled for r in rules):
            self.seen.update(x.key for x in fresh)
            return res
        books: dict[tuple[str, Market], list[Listing]] = {}
        for x in fresh:
            for c in self.clients:
                key = (x.collection, c.market)
                if key not in books:
                    books[key] = (
                        await self._safe(
                            c.search(
                                SearchQuery(
                                    collection=x.collection, sort="price_asc", limit=self.book_limit
                                )
                            ),
                            c.market,
                            res.errors,
                        )
                        or []
                    )
            deal: Deal = evaluate(
                x,
                {c.market: books[(x.collection, c.market)] for c in self.clients},
                self.sales,
                now,
            )
            res.evaluated += 1
            matches = match_presets(deal, rules)
            if matches and await self.notifier.notify(self.owner_chat_id, deal, matches[0]):
                res.notified += 1
            self.seen.add(x.key)
        # продажи старше суток для медианы не нужны
        self.sales = [s for s in self.sales if (now - s.occurred_at).total_seconds() <= 86_400]
        return res
