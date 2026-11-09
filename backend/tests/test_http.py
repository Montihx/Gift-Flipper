import random
from decimal import Decimal

import pytest

from app.markets.base import MarketError
from app.markets.http import (
    HttpError,
    ReadOnlyGuard,
    ReadOnlyViolation,
    RetryPolicy,
    Route,
    Throttle,
)
from tests.conftest import FakeTransport, ok

ROUTES = [Route("GET", r"/api/items"), Route("POST", r"/api/search")]
BASE = "https://example.invalid/api/"


async def test_parses_floats_as_decimal(make_http):
    t = FakeTransport().add("GET", "/api/items", ok(raw=b'{"price": 5.5}'))
    data = await make_http("x", BASE, ROUTES, t).get_json("items")
    assert data["price"] == Decimal("5.5")
    assert isinstance(data["price"], Decimal)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/items"),  # метод не тот
        ("GET", "/api/nfts"),  # путь не в списке
        ("POST", "/api/gifts/buy"),
        ("POST", "/api/buyGift/42"),
    ],
)
async def test_guard_blocks_unlisted(make_http, method, path):
    t = FakeTransport()
    http = make_http("x", BASE, ROUTES, t)
    with pytest.raises(ReadOnlyViolation):
        await http.request(method, "https://example.invalid" + path)
    assert t.sent == []  # запрос не ушёл


async def test_retry_after_429_then_ok(make_http, no_sleep):
    t = FakeTransport().add(
        "GET", "/api/items", ok({}, status=429, headers={"retry-after": "7"}), ok({"a": 1})
    )
    http = make_http("x", BASE, ROUTES, t)
    assert await http.get_json("items") == {"a": 1}
    assert 7.0 in no_sleep.calls
    assert http.metrics.rate_limited == 1
    assert http.metrics.retries == 1


async def test_5xx_exhausts_attempts(make_http):
    t = FakeTransport().add("GET", "/api/items", ok({}, status=502))
    http = make_http("x", BASE, ROUTES, t, attempts=3)
    with pytest.raises(HttpError) as exc:
        await http.get_json("items")
    assert exc.value.status == 502
    assert len(t.sent) == 3


async def test_4xx_not_retried(make_http):
    t = FakeTransport().add("GET", "/api/items", ok({}, status=404))
    http = make_http("x", BASE, ROUTES, t)
    with pytest.raises(HttpError):
        await http.get_json("items")
    assert len(t.sent) == 1


async def test_network_error_retried(make_http):
    calls = {"n": 0}

    def flaky(_):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("timeout")
        return ok({"ok": True})

    t = FakeTransport().add("GET", "/api/items", flaky)
    assert await make_http("x", BASE, ROUTES, t).get_json("items") == {"ok": True}


async def test_non_json_is_market_error(make_http):
    t = FakeTransport().add("GET", "/api/items", ok(raw=b"<html>cf</html>"))
    with pytest.raises(MarketError):
        await make_http("x", BASE, ROUTES, t).get_json("items")


@pytest.mark.parametrize(
    ("attempt", "retry_after", "expected_range"),
    [
        (0, "30", (30.0, 30.0)),
        (0, "0", (1.0, 1.0)),  # не меньше 1 с
        (0, "9999", (300.0, 300.0)),  # не больше max
        (0, None, (1.0, 2.0)),  # base 2 с, jitter 50–100%
        (3, None, (8.0, 16.0)),  # 2·2³ = 16
        (10, None, (150.0, 300.0)),  # потолок 300
    ],
)
def test_retry_delay(attempt, retry_after, expected_range):
    d = RetryPolicy(base_s=2.0, max_s=300.0).delay(attempt, retry_after, random.Random(1))
    lo, hi = expected_range
    assert lo <= d <= hi


async def test_throttle_spacing():
    now = {"t": 100.0}
    slept: list[float] = []

    async def sleep(s):
        slept.append(s)
        now["t"] += s

    th = Throttle(5.0, clock=lambda: now["t"], sleep=sleep)
    await th.wait()
    await th.wait()
    now["t"] += 1.0
    await th.wait()
    assert slept == [5.0, 4.0]


def test_guard_route_fullmatch():
    g = ReadOnlyGuard([Route("GET", r"/api/nfts/search")])
    with pytest.raises(ReadOnlyViolation):
        g.check("GET", "https://x/api/nfts/search/../../buy")
