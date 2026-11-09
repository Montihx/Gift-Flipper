"""Сопоставление `Deal` с пресетами и дедуп уведомлений (PLAN 4.3).

Режим сделки: `watch`, пока живая торговля не разрешена или комиссии пары не проверены
(D-003, D-009). Пресет может просить confirm/auto — это записывается, но исполняется watch.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.pricing.aliases import same_collection
from app.pricing.deal import Deal
from app.rules.filters import DealFilter, Mode
from app.rules.traits import is_beautiful, is_monochrome
from app.settings import LIVE_TRADING_ALLOWED

_CONF_RANK = {"low": 0, "med": 1, "high": 2}


@dataclass(frozen=True, slots=True)
class PresetRule:
    id: int
    name: str
    priority: int  # больше — важнее
    enabled: bool
    mode: Mode
    filter: DealFilter


@dataclass(frozen=True, slots=True)
class Match:
    preset: PresetRule
    effective_mode: Mode


def _in(value: str | None, allowed: list[str]) -> bool:
    return not allowed or (
        value is not None and value.casefold() in {a.casefold() for a in allowed}
    )


def _rarity_ok(value: int | None, limit: int | None) -> bool:
    return limit is None or (value is not None and value <= limit)


def reasons_rejected(deal: Deal, f: DealFilter, monochrome_score: int | None = None) -> list[str]:
    """Пустой список — сделка проходит фильтр. Коды причин — для журнала и `/why`."""
    x = deal.listing
    r: list[str] = []
    if f.markets and x.market not in f.markets:
        r.append("market")
    if f.collections and not any(same_collection(x.collection, c) for c in f.collections):
        r.append("collection")
    if not _in(x.model, f.models):
        r.append("model")
    if not _in(x.backdrop, f.backdrops):
        r.append("backdrop")
    if not _in(x.symbol, f.symbols):
        r.append("symbol")
    if not _rarity_ok(x.model_rarity_pm, f.max_model_rarity_pm):
        r.append("model_rarity")
    if not _rarity_ok(x.backdrop_rarity_pm, f.max_backdrop_rarity_pm):
        r.append("backdrop_rarity")
    if not _rarity_ok(x.symbol_rarity_pm, f.max_symbol_rarity_pm):
        r.append("symbol_rarity")
    n = f.number
    if (n.min is not None or n.max is not None or n.max_distinct_digits) and x.number is None:
        r.append("number")
    elif x.number is not None:
        if (n.min is not None and x.number < n.min) or (n.max is not None and x.number > n.max):
            r.append("number_range")
        if n.max_distinct_digits and not is_beautiful(x.number, n.max_distinct_digits):
            r.append("number_digits")
    if f.monochrome_only and not is_monochrome(monochrome_score):
        r.append("monochrome")
    if f.min_price_nano is not None and deal.all_in_nano < f.min_price_nano:
        r.append("price_min")
    if f.max_price_nano is not None and deal.all_in_nano > f.max_price_nano:
        r.append("price_max")
    best = deal.best
    if best is None:
        r.append("no_floor")
    else:
        if _CONF_RANK[best.floor.confidence] < _CONF_RANK[f.min_confidence]:
            r.append("confidence")
        if f.min_comparables is not None and best.floor.comparables < f.min_comparables:
            r.append("comparables")
    if f.min_discount_bps is not None and (
        deal.discount_bps is None or deal.discount_bps < f.min_discount_bps
    ):
        r.append("discount")
    if f.min_profit_nano is not None and (
        deal.profit_nano is None or deal.profit_nano < f.min_profit_nano
    ):
        r.append("profit")
    if f.min_roi_bps is not None and (deal.roi_bps is None or deal.roi_bps < f.min_roi_bps):
        r.append("roi")
    e = f.exclude
    if e.auctions and x.is_auction:
        r.append("auction")
    if e.premarket and x.is_premarket:
        r.append("premarket")
    if e.locked and deal.locked:
        r.append("locked")
    if e.bundles and x.is_bundle:
        r.append("bundle")
    if e.too_good and deal.too_good:
        r.append("too_good")
    return r


def effective_mode(requested: Mode, deal: Deal) -> Mode:
    if requested == "watch" or not LIVE_TRADING_ALLOWED or deal.estimate:
        return "watch"
    return requested


def match_presets(
    deal: Deal, presets: Iterable[PresetRule], monochrome_score: int | None = None
) -> list[Match]:
    """Подходящие включённые пресеты, по убыванию приоритета (при равенстве — по id)."""
    hits = [
        Match(p, effective_mode(p.mode, deal))
        for p in presets
        if p.enabled and not reasons_rejected(deal, p.filter, monochrome_score)
    ]
    return sorted(hits, key=lambda m: (-m.preset.priority, m.preset.id))


class Deduper:
    """Повторное уведомление — только при строго меньшей цене (из кода topcvetok, D-015).

    Ключ — (чат, маркет, id листинга). Хранится в памяти; персистентная версия — таблица
    `alerts` (Этап 5).
    """

    def __init__(self) -> None:
        self._last: dict[tuple[int, str, str], int] = {}

    def should_notify(self, chat_id: int, deal: Deal) -> bool:
        key = (chat_id, deal.listing.market, deal.listing.listing_id)
        old = self._last.get(key)
        if old is not None and deal.listing.price_nano >= old:
            return False
        self._last[key] = deal.listing.price_nano
        return True
