"""Сборка клиентов маркетов из настроек."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.markets import mrkt, portals, tonnel
from app.markets.base import Market, MarketClient
from app.markets.http import (
    CurlTransport,
    MarketHttp,
    ReadOnlyGuard,
    RetryPolicy,
    Throttle,
    Transport,
)
from app.settings import Settings

# Опыт topcvetok: ≥1,2 с между запросами к Portals (portals_watch.py:47).
MIN_INTERVAL_OVERRIDE: dict[Market, float] = {"portals": 1.2}

_SPEC = {
    "portals": (portals.BASE_URL, portals.HEADERS, portals.READ_ROUTES),
    "mrkt": (mrkt.BASE_URL, mrkt.HEADERS, mrkt.READ_ROUTES),
    "tonnel": (tonnel.BASE_URL, tonnel.HEADERS, tonnel.READ_ROUTES),
}


def make_http(market: Market, settings: Settings, transport: Transport | None = None) -> MarketHttp:
    base, headers, routes = _SPEC[market]
    interval = max(settings.market_min_interval_s, MIN_INTERVAL_OVERRIDE.get(market, 0.0))
    return MarketHttp(
        market,
        base,
        transport or CurlTransport(),
        ReadOnlyGuard(routes),
        headers=headers,
        throttle=Throttle(interval),
        retry=RetryPolicy(base_s=settings.backoff_base_s, max_s=settings.backoff_max_s),
        timeout_s=settings.request_timeout_s,
    )


def make_client(
    market: Market,
    settings: Settings,
    init_data: Callable[[], Awaitable[str]] | None = None,
    transport: Transport | None = None,
) -> MarketClient:
    http = make_http(market, settings, transport)
    if market == "portals":
        return portals.PortalsClient(http, auth=init_data)
    if market == "mrkt":
        if init_data is None:
            raise ValueError("mrkt: нужен initData (все маршруты за авторизацией)")
        return mrkt.MrktClient(http, init_data)
    return tonnel.TonnelClient(http, init_data)
