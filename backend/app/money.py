"""Деньги: внутри только nanoTON (int), TON (Decimal) — на отображении (AGENTS.md §5, D-012).

float на входе запрещён: маркеты отдают цены строкой (Portals), числом JSON (Tonnel) или
nanoTON (MRKT). JSON-числа нужно парсить как Decimal (`json.loads(..., parse_float=Decimal)`)
или передавать строкой.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, InvalidOperation

NANO_PER_TON = 1_000_000_000

Nano = int


def ton_to_nano(value: str | int | Decimal) -> Nano:
    """TON → nanoTON без потерь. Дробная часть точнее 1e-9 TON — ошибка, а не округление."""
    if isinstance(value, (bool, float)):
        raise TypeError("float/bool для денег запрещены; передайте str, int или Decimal")
    try:
        dec = Decimal(value.strip()) if isinstance(value, str) else Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"не число: {value!r}") from exc
    if not dec.is_finite():
        raise ValueError(f"не конечное число: {value!r}")
    nano = dec * NANO_PER_TON
    if nano != nano.to_integral_value():
        raise ValueError(f"точность выше 1 nanoTON: {value!r}")
    return int(nano)


def nano_to_ton(nano: Nano) -> Decimal:
    if isinstance(nano, bool) or not isinstance(nano, int):
        raise TypeError("nanoTON должен быть int")
    return Decimal(nano) / NANO_PER_TON


def format_ton(nano: Nano, places: int = 2) -> str:
    """Для показа: усечение вниз до `places` знаков, без экспоненты."""
    quant = Decimal(1).scaleb(-places)
    return f"{nano_to_ton(nano).quantize(quant, rounding=ROUND_DOWN):f}"


def apply_bps(nano: Nano, bps: int) -> Nano:
    """Доля в базисных пунктах (1% = 100 bps), округление вниз к целому nanoTON."""
    if bps < 0:
        raise ValueError("bps < 0")
    return nano * bps // 10_000
