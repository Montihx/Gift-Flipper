"""Список запросов живого режима — показывается владельцу ДО запуска (задание, Этап 2).

Только чтение. Для каждого запроса — метод, URL, что в теле (без секретов) и сколько раз
за цикл. Источник формата — MARKETS.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.markets import mrkt, portals, tonnel


@dataclass(frozen=True, slots=True)
class PlannedRequest:
    market: str
    method: str
    url: str
    body: str
    auth: str
    per_cycle: str


def live_plan(collections: list[str]) -> list[PlannedRequest]:
    cols = ", ".join(collections) or "без фильтра"
    p, m, t = portals.BASE_URL, mrkt.BASE_URL, tonnel.BASE_URL
    return [
        PlannedRequest(
            "portals", "GET", p + "collections?limit=100", "—", "нет", "1 раз при старте"
        ),
        PlannedRequest(
            "portals",
            "GET",
            p + "nfts/search",
            f"query: {cols}, sort listed_at desc, status=listed, limit≤20",
            "нет",
            "1 на коллекцию",
        ),
        PlannedRequest(
            "portals",
            "GET",
            p + "market/actions/",
            "query: action_types=buy, limit≤20",
            "Authorization: tma <initData>",
            "1",
        ),
        PlannedRequest(
            "mrkt",
            "POST",
            m + "auth",
            '{"data": <initData>}',
            "initData в теле",
            "1 при старте и при 401",
        ),
        PlannedRequest(
            "mrkt",
            "POST",
            m + "gifts/saling",
            f"collectionNames: [{cols}], count≤20",
            "Authorization + Cookie access_token",
            "1 на коллекцию",
        ),
        PlannedRequest("mrkt", "GET", m + "gifts/collections", "—", "Authorization", "1"),
        PlannedRequest(
            "mrkt", "POST", m + "feed", 'type: ["Sale"], count≤20', "Authorization", "1"
        ),
        PlannedRequest(
            "tonnel",
            "POST",
            t + "pageGifts",
            f'filter: активные TON-лоты {cols}, limit≤30, user_auth=""',
            "нет",
            "1 на коллекцию",
        ),
        PlannedRequest(
            "tonnel",
            "POST",
            t + "filterStats",
            '{"authData": <initData>}',
            "initData в теле (только если задан бот Tonnel)",
            "1",
        ),
        PlannedRequest(
            "tonnel", "WS", tonnel.EVENTS_WS_URL, "только приём событий", "нет", "1 соединение"
        ),
        PlannedRequest(
            "tonnel",
            "GET",
            tonnel.EVENTS_URL,
            "query: after=<eventId>, limit=100",
            "нет",
            "только после обрыва WS",
        ),
        PlannedRequest(
            "telegram",
            "MTProto",
            "messages.requestAppWebView",
            "@portals/market, @mrkt/app",
            "сессия владельца",
            "1 на маркет при старте",
        ),
    ]


def format_plan(plan: list[PlannedRequest], interval_s: float) -> str:
    lines = [
        "Запросы живого режима (только чтение; покупка/листинг/вывод запрещены HTTP-слоем):",
        f"Бюджет D-008: ≤1 запрос/с на маркет, опрос листингов раз в {interval_s:g} с.",
        "",
    ]
    for i, r in enumerate(plan, 1):
        lines.append(f"{i:2}. [{r.market}] {r.method} {r.url}")
        lines.append(f"      тело/параметры: {r.body}")
        lines.append(f"      авторизация: {r.auth}; частота: {r.per_cycle}")
    return "\n".join(lines)
