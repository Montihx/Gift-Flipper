"""Снимок `Deal` в JSON для Mini App. Деньги: `*_nano` — строки (точность в JS),
`*_ton` — строки для показа."""

from __future__ import annotations

from typing import Any

from app.money import format_ton
from app.pricing.deal import Deal, ResaleOption


def _money(nano: int | None) -> dict[str, str | None]:
    if nano is None:
        return {"nano": None, "ton": None}
    return {"nano": str(nano), "ton": format_ton(nano)}


def _option(o: ResaleOption) -> dict[str, Any]:
    return {
        "market": o.market,
        "floor": _money(o.floor.floor_nano),
        "basis": o.floor.basis,
        "confidence": o.floor.confidence,
        "comparables": o.floor.comparables,
        "method": o.floor.method,
        "resale": _money(o.resale_nano),
        "net": _money(o.net_nano),
        "sales_count": o.sales_count,
        "capped_by_sales": o.capped_by_sales,
    }


def deal_snapshot(deal: Deal) -> dict[str, Any]:
    x = deal.listing
    return {
        "listing": {
            "market": x.market,
            "listing_id": x.listing_id,
            "collection": x.collection,
            "model": x.model,
            "backdrop": x.backdrop,
            "symbol": x.symbol,
            "number": x.number,
            "price": _money(x.price_nano),
            "url": x.url,
            "rarity_pm": {
                "model": x.model_rarity_pm,
                "backdrop": x.backdrop_rarity_pm,
                "symbol": x.symbol_rarity_pm,
            },
        },
        "all_in": _money(deal.all_in_nano),
        "best": _option(deal.best) if deal.best else None,
        "options": [_option(o) for o in deal.options],
        "profit": _money(deal.profit_nano),
        "roi_bps": deal.roi_bps,
        "discount_bps": deal.discount_bps,
        "estimate": deal.estimate,
        "too_good": deal.too_good,
        "locked": deal.locked,
        "cheapest_elsewhere": {m: _money(v) for m, v in deal.cheapest_elsewhere.items()},
        "cheaper_elsewhere": deal.cheaper_elsewhere,
        "tg_above_value": deal.tg_above_value,
    }
