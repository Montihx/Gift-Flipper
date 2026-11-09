"""Оценка Telegram — вспомогательный сигнал (PLAN 3.4, D-010).

`payments.getUniqueStarGiftValueInfo(slug)` (SUMMARY.md §3): суммы в наименьших единицах
фиатной валюты `currency`; для сравнения с TON нужен курс (погрешность). Решение по
оценке Telegram само не принимается; правило из README раздела I: если цена выше и
средней, и последней продажи по Telegram при флоре с доверием low — не автоматом, спросить.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_DOWN, Decimal
from typing import Any

from app.money import NANO_PER_TON
from app.timeutil import from_unix

# ISO 4217: валюты без дробной части. Остальные — 2 знака.
ZERO_DECIMAL = frozenset({"JPY", "KRW", "VND", "CLP", "ISK", "UGX", "PYG", "XAF", "XOF"})


def minor_to_major(amount: int, currency: str) -> Decimal:
    exp = 0 if currency.upper() in ZERO_DECIMAL else 2
    return Decimal(amount).scaleb(-exp)


@dataclass(frozen=True, slots=True)
class TgValue:
    currency: str
    value: int
    value_is_average: bool
    floor_price: int | None
    average_price: int | None
    last_sale_price: int | None
    last_sale_date: datetime | None
    listed_count: int | None


def parse_value_info(obj: Any) -> TgValue:
    """Объект Telethon `payments.UniqueStarGiftValueInfo` → TgValue (поля из схемы слоя 212)."""
    last = getattr(obj, "last_sale_date", None)
    if isinstance(last, int):
        last = from_unix(last)
    return TgValue(
        currency=str(obj.currency),
        value=int(obj.value),
        value_is_average=bool(getattr(obj, "value_is_average", False)),
        floor_price=getattr(obj, "floor_price", None),
        average_price=getattr(obj, "average_price", None),
        last_sale_price=getattr(obj, "last_sale_price", None),
        last_sale_date=last,
        listed_count=getattr(obj, "listed_count", None),
    )


def fiat_minor_to_nano(amount: int, currency: str, fiat_per_ton: Decimal) -> int:
    """Сумма в минимальных единицах фиата → nanoTON по курсу «фиат за 1 TON»."""
    if fiat_per_ton <= 0:
        raise ValueError("курс должен быть > 0")
    ton = minor_to_major(amount, currency) / fiat_per_ton
    return int((ton * NANO_PER_TON).to_integral_value(rounding=ROUND_DOWN))


def above_telegram_value(all_in_nano: int, tg: TgValue, fiat_per_ton: Decimal) -> bool | None:
    """True — цена выше и средней, и последней продажи по Telegram; None — данных нет."""
    if tg.average_price is None or tg.last_sale_price is None:
        return None
    avg = fiat_minor_to_nano(tg.average_price, tg.currency, fiat_per_ton)
    last = fiat_minor_to_nano(tg.last_sale_price, tg.currency, fiat_per_ton)
    return all_in_nano > avg and all_in_nano > last


async def fetch_value_info(client: Any, slug: str) -> TgValue:
    """Запрос через Telethon (только пользовательская сессия)."""
    from telethon.tl.functions.payments import (
        GetUniqueStarGiftValueInfoRequest,
    )

    return parse_value_info(await client(GetUniqueStarGiftValueInfoRequest(slug=slug)))
