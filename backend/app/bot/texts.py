"""Тексты уведомлений (HTML Telegram). Прибыль до проверки комиссий — «оценка» (D-009)."""

from __future__ import annotations

from html import escape

from app.markets.base import Market
from app.money import format_ton
from app.pricing.deal import Deal

MARKET_TITLE: dict[Market, str] = {"portals": "Portals", "mrkt": "MRKT", "tonnel": "Tonnel"}
BASIS_TITLE = {"model_backdrop": "модель+фон", "model": "модель", "collection": "коллекция"}
CONF_TITLE = {"high": "высокое", "med": "среднее", "low": "низкое"}


def _pct(bps: int | None) -> str:
    return "—" if bps is None else f"{bps / 100:.1f}%"


def format_deal(deal: Deal, preset_name: str | None = None) -> str:
    x = deal.listing
    num = f" #{x.number}" if x.number is not None else ""
    attrs = " · ".join(escape(a) for a in (x.model, x.backdrop, x.symbol) if a)
    lines = [f"🟢 <b>{escape(x.collection)}{num}</b> · {MARKET_TITLE[x.market]}"]
    if attrs:
        lines.append(attrs)
    lines.append(
        f"Цена: <b>{format_ton(x.price_nano)} TON</b> (с комиссией {format_ton(deal.all_in_nano)})"
    )
    if deal.best is not None:
        f = deal.best.floor
        own = next((o for o in deal.options if o.market == x.market), None)
        if own is not None:
            lines.append(
                f"Флор: {format_ton(own.floor.floor_nano)} TON ({BASIS_TITLE[own.floor.basis]}, "
                f"доверие {CONF_TITLE[own.floor.confidence]}, {own.floor.comparables} шт.)"
            )
        lines.append(f"Ниже флора: {_pct(deal.discount_bps)}")
        label = "оценка, комиссии не проверены" if deal.estimate else "комиссии проверены"
        lines.append(
            f"Прибыль: <b>~{format_ton(deal.profit_nano or 0)} TON</b> ({_pct(deal.roi_bps)}) — "
            f"{label}; продажа на {MARKET_TITLE[deal.best.market]} "
            f"по {format_ton(deal.best.resale_nano)} (флор {format_ton(f.floor_nano)})"
        )
        if deal.best.capped_by_sales:
            lines.append(f"Ограничено медианой продаж за 24 ч ({deal.best.sales_count} шт.)")
    cheaper = deal.cheaper_elsewhere
    if cheaper is not None:
        lines.append(
            f"⚠️ Дешевле на {MARKET_TITLE[cheaper]}: "
            f"{format_ton(deal.cheapest_elsewhere[cheaper])} TON с комиссией"
        )
    if deal.tg_above_value:
        lines.append("⚠️ Выше средней и последней продажи по оценке Telegram")
    if preset_name:
        lines.append(f"Пресет: {escape(preset_name)}")
    return "\n".join(lines)


def format_sold(text: str, sold_price_nano: int | None = None) -> str:
    head = "🔴 <b>ПРОДАНО</b>"
    if sold_price_nano is not None:
        head += f" за {format_ton(sold_price_nano)} TON"
    return head + "\n" + text.removeprefix("🟢 ")


def format_gone(text: str) -> str:
    return "⚪️ <b>Снято с продажи</b>\n" + text.removeprefix("🟢 ")


def format_price_changed(new_text: str, old_nano: int, new_nano: int) -> str:
    arrow = "снизилась" if new_nano < old_nano else "выросла"
    return (
        f"🟡 Цена {arrow}: {format_ton(old_nano)} → <b>{format_ton(new_nano)} TON</b>\n"
        + new_text.removeprefix("🟢 ")
    )
