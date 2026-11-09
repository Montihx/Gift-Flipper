from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

from app.markets.http import MarketHttp, ReadOnlyGuard, Response, RetryPolicy, Throttle

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    """JSON фикстуры; дробные числа — Decimal, как в боевом парсере."""
    return json.loads((FIXTURES / name).read_text("utf-8"), parse_float=Decimal)


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@dataclass
class Sent:
    method: str
    url: str
    params: Any
    json_body: Any
    headers: dict[str, str]

    @property
    def path(self) -> str:
        return urlsplit(self.url).path


@dataclass
class FakeTransport:
    """Отвечает по (метод, путь). Значение — Response или функция(Sent) -> Response."""

    routes: dict[tuple[str, str], list[Response | Callable[[Sent], Response]]] = field(
        default_factory=dict
    )
    sent: list[Sent] = field(default_factory=list)
    closed: bool = False

    def add(self, method: str, path: str, *responses: Response | Callable[[Sent], Response]):
        self.routes.setdefault((method, path), []).extend(responses)
        return self

    async def request(self, method, url, *, params, json_body, headers, timeout):
        s = Sent(method, url, params, json_body, dict(headers))
        self.sent.append(s)
        queue = self.routes.get((method, s.path))
        if not queue:
            raise AssertionError(f"нет ответа для {method} {s.path}")
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        return item(s) if callable(item) else item

    async def aclose(self):
        self.closed = True


def ok(body: Any = None, *, raw: bytes | None = None, status: int = 200, headers=None) -> Response:
    data = raw if raw is not None else json.dumps(body, default=str).encode()
    return Response(status, headers or {}, data)


def ok_fixture(name: str) -> Response:
    return Response(200, {}, fixture_bytes(name))


class NoSleep:
    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


@pytest.fixture
def no_sleep() -> NoSleep:
    return NoSleep()


@pytest.fixture
def make_http(no_sleep):
    def _make(market, base_url, routes, transport, headers=None, attempts=3):
        return MarketHttp(
            market,
            base_url,
            transport,
            ReadOnlyGuard(routes),
            headers=headers,
            throttle=Throttle(0.0, sleep=no_sleep),
            retry=RetryPolicy(attempts=attempts, base_s=1.0, max_s=60.0),
            sleep=no_sleep,
        )

    return _make
