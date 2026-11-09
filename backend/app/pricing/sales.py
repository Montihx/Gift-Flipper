"""Проверка флора продажами за 24 ч (PLAN 3.2).

Правило (из кода topcvetok tonnel_watch.py:545-587, D-015): если по тому же основанию
(модель+фон / модель / коллекция) за 24 ч было ≥3 продаж, цена перепродажи =
min(флор, медиана продаж). Медиана классическая; для чётного числа — среднее двух средних,
округлённое вниз до nanoTON.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.markets.base import Listing, Sale
from app.pricing.floor import Basis


@dataclass(frozen=True, slots=True)
class SalesCheck:
    count: int
    median_nano: int | None
    resale_nano: int  # итоговая цена перепродажи
    capped_by_sales: bool


def median(values: list[int]) -> int:
    if not values:
        raise ValueError("пустой список")
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) // 2


def matching_sales(
    target: Listing,
    sales: Iterable[Sale],
    basis: Basis,
    now: datetime,
    window: timedelta = timedelta(hours=24),
) -> list[int]:
    since = now - window
    out = []
    for s in sales:
        if s.collection != target.collection or not (since <= s.occurred_at <= now):
            continue
        if basis in ("model", "model_backdrop") and s.model != target.model:
            continue
        if basis == "model_backdrop" and s.backdrop != target.backdrop:
            continue
        out.append(s.price_nano)
    return out


def check_with_sales(floor_nano: int, sale_prices: list[int], min_count: int = 3) -> SalesCheck:
    if len(sale_prices) < min_count:
        return SalesCheck(len(sale_prices), None, floor_nano, False)
    med = median(sale_prices)
    return SalesCheck(len(sale_prices), med, min(floor_nano, med), med < floor_nano)
