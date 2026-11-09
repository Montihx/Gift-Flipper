"""Флор по сопоставимым (PLAN 3.1, AGENTS.md §8).

Алгоритм (наш, по определениям AGENTS.md §8 и идеям из SUMMARY.md §2):
1. Уровни сопоставимых от узкого к широкому: модель+фон → модель → коллекция.
   Берётся первый уровень, где сопоставимых ≥ `min_comparables` (3 для атрибутов, 5 для
   коллекции — как у topcvetok).
2. Сопоставимые = активные листинги той же коллекции, кроме самого лота, бандлов,
   премаркета и аукционов.
3. Кластерный флор: минимальная цена p, у которой есть ещё ≥2 объявления в [p, p·1.1].
   Доверие: high — кластер и ≥8 сопоставимых; med — кластер; low — кластера нет, флор =
   медиана трёх самых дешёвых (идея из README раздела I).
4. Скачок флора > 25% относительно предыдущего значения — доверие на ступень ниже.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import Literal

from app.markets.base import Listing

Basis = Literal["model_backdrop", "model", "collection"]
Confidence = Literal["high", "med", "low"]
_DOWNGRADE: dict[Confidence, Confidence] = {"high": "med", "med": "low", "low": "low"}


@dataclass(frozen=True, slots=True)
class FloorConfig:
    cluster_k: int = 3
    cluster_band_bps: int = 1000
    min_comparables_attr: int = 3
    min_comparables_collection: int = 5
    high_min_comparables: int = 8
    jump_bps: int = 2500
    too_good_bps: int = 2500


@dataclass(frozen=True, slots=True)
class FloorEstimate:
    floor_nano: int
    basis: Basis
    confidence: Confidence
    comparables: int
    cluster_size: int
    method: Literal["cluster", "thin_median"]


def cluster_floor(sorted_prices: list[int], k: int, band_bps: int) -> tuple[int, int] | None:
    """(флор, размер кластера) или None. Цены отсортированы по возрастанию."""
    n = len(sorted_prices)
    j = 0
    for i, p in enumerate(sorted_prices):
        limit = p * (10_000 + band_bps)
        j = max(j, i)
        while j + 1 < n and sorted_prices[j + 1] * 10_000 <= limit:
            j += 1
        size = j - i + 1
        if size >= k:
            return p, size
    return None


def is_comparable(item: Listing) -> bool:
    return not (item.is_bundle or item.is_premarket or item.is_auction)


def _levels(target: Listing) -> list[Basis]:
    levels: list[Basis] = []
    if target.model and target.backdrop:
        levels.append("model_backdrop")
    if target.model:
        levels.append("model")
    levels.append("collection")
    return levels


def _matches(basis: Basis, target: Listing, item: Listing) -> bool:
    if basis == "model_backdrop":
        return item.model == target.model and item.backdrop == target.backdrop
    if basis == "model":
        return item.model == target.model
    return True


def _median3(prices: list[int]) -> int:
    cheapest = prices[:3]
    return cheapest[len(cheapest) // 2] if len(cheapest) % 2 else ((cheapest[0] + cheapest[1]) // 2)


def estimate_floor(
    target: Listing, book: Iterable[Listing], cfg: FloorConfig | None = None
) -> FloorEstimate | None:
    cfg = cfg or FloorConfig()
    pool = [
        x
        for x in book
        if x.collection == target.collection
        and x.market == target.market
        and x.listing_id != target.listing_id
        and is_comparable(x)
    ]
    for basis in _levels(target):
        prices = sorted(x.price_nano for x in pool if _matches(basis, target, x))
        need = cfg.min_comparables_collection if basis == "collection" else cfg.min_comparables_attr
        if len(prices) < need:
            continue
        found = cluster_floor(prices, cfg.cluster_k, cfg.cluster_band_bps)
        if found is None:
            return FloorEstimate(_median3(prices), basis, "low", len(prices), 0, "thin_median")
        floor, size = found
        conf: Confidence = "high" if len(prices) >= cfg.high_min_comparables else "med"
        return FloorEstimate(floor, basis, conf, len(prices), size, "cluster")
    return None


def jump_adjusted(
    est: FloorEstimate, previous_floor_nano: int | None, cfg: FloorConfig | None = None
) -> FloorEstimate:
    cfg = cfg or FloorConfig()
    if not previous_floor_nano:
        return est
    change = abs(est.floor_nano - previous_floor_nano) * 10_000
    if change > cfg.jump_bps * previous_floor_nano:
        return replace(est, confidence=_DOWNGRADE[est.confidence])
    return est


def looks_too_good(price_nano: int, floor_nano: int, cfg: FloorConfig | None = None) -> bool:
    """Цена ниже 25% флора — вероятная ошибка/ловушка, автоматически не покупаем."""
    cfg = cfg or FloorConfig()
    return price_nano * 10_000 < cfg.too_good_bps * floor_nano
