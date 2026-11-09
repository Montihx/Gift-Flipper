"""Комиссии маркетов: конфигурация с флагом «проверено» (D-009, MARKETS.md §6).

Все значения по умолчанию — `verified=False`. Где источники расходятся, берётся наибольшая
заявленная комиссия (консервативная оценка). Пока хоть одна сторона сделки не проверена,
прибыль показывается как «оценка», а режимы confirm/auto для пары маркетов не включаются.
Проверенную таблицу присылает владелец (условие Этапа 7).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.markets.base import Market
from app.money import apply_bps


@dataclass(frozen=True, slots=True)
class FeeSchedule:
    buy_bps: int  # надбавка к цене листинга при покупке
    sell_bps: int  # удержание с цены продажи
    withdraw_nano: int  # фиксированная плата за вывод с маркета
    verified: bool
    source: str

    def __post_init__(self) -> None:
        for name in ("buy_bps", "sell_bps"):
            v = getattr(self, name)
            if not 0 <= v <= 10_000:
                raise ValueError(f"{name} вне 0..10000: {v}")
        if self.withdraw_nano < 0:
            raise ValueError("withdraw_nano < 0")


DEFAULT_FEES: dict[Market, FeeSchedule] = {
    "portals": FeeSchedule(
        buy_bps=0,
        sell_bps=500,
        withdraw_nano=100_000_000,
        verified=False,
        source="заявлено: README раздела I (0%/5%/0.1 TON); vc.ru — продажа 2.5%; берём 5%",
    ),
    "tonnel": FeeSchedule(
        buy_bps=1000,
        sell_bps=400,
        withdraw_nano=1_000_000,
        verified=False,
        source="README tonnelmp: покупка price×1.1; продажа 0% (раздел I) / 3–4% (dev.to) — "
        "берём 4%; вывод 0.001 TON (докстринг tonnelmp)",
    ),
    "mrkt": FeeSchedule(
        buy_bps=0,
        sell_bps=800,
        withdraw_nano=0,
        verified=False,
        source="покупка: salePrice уже включает ~2% (фикстура topcvetok salePriceWithoutFee=/1.02);"
        " продажа 2%/5%/«8%» (статьи, morgan) — берём 8%; вывод не установлен",
    ),
}


def schedule(market: Market, fees: dict[Market, FeeSchedule] | None = None) -> FeeSchedule:
    return (fees or DEFAULT_FEES)[market]


def all_in_price(
    market: Market, price_nano: int, fees: dict[Market, FeeSchedule] | None = None
) -> int:
    """Сколько реально заплатим за листинг (AGENTS.md §8, «All-in»)."""
    s = schedule(market, fees)
    return price_nano + apply_bps(price_nano, s.buy_bps)


def net_after_sale(
    market: Market, resale_nano: int, fees: dict[Market, FeeSchedule] | None = None
) -> int:
    """Что останется после продажи по `resale_nano` и вывода (AGENTS.md §8, «Net»)."""
    s = schedule(market, fees)
    net = resale_nano - apply_bps(resale_nano, s.sell_bps) - s.withdraw_nano
    return max(net, 0)


def verified_pair(buy: Market, sell: Market, fees: dict[Market, FeeSchedule] | None = None) -> bool:
    return schedule(buy, fees).verified and schedule(sell, fees).verified
