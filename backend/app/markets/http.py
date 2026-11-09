"""HTTP-слой маркетов: throttle, backoff, таймауты, метрики, запрет записи (PLAN 2.6).

- Транспорт подменяется в тестах (`FakeTransport`); реальный — curl_cffi с имитацией
  браузерного TLS (D-006).
- `ReadOnlyGuard` пропускает только явно разрешённые пары (метод, путь). Пути покупки,
  листинга, вывода сюда не попадают: их вызов возможен только через `execution.spend()`
  (Этап 7, AGENTS.md §4.1).
- JSON парсится с `parse_float=Decimal`: дробные цены Tonnel не проходят через float.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol
from urllib.parse import urlsplit

from app.markets.base import MarketError
from app.security import mask_secrets

log = logging.getLogger(__name__)

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class Response:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def json(self) -> Any:
        try:
            return json.loads(self.body, parse_float=Decimal)
        except (ValueError, UnicodeDecodeError) as exc:
            raise MarketError(f"не JSON (HTTP {self.status})") from exc


class Transport(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None,
        json_body: Any,
        headers: Mapping[str, str],
        timeout: float,
    ) -> Response: ...

    async def aclose(self) -> None: ...


class CurlTransport:
    """curl_cffi AsyncSession с имитацией TLS браузера (D-006)."""

    def __init__(self, impersonate: str = "chrome", proxy: str | None = None) -> None:
        from curl_cffi.requests import AsyncSession

        self._session = AsyncSession(impersonate=impersonate, proxy=proxy)

    async def request(self, method, url, *, params, json_body, headers, timeout) -> Response:
        r = await self._session.request(
            method, url, params=params, json=json_body, headers=dict(headers), timeout=timeout
        )
        return Response(r.status_code, {k.lower(): v for k, v in r.headers.items()}, r.content)

    async def aclose(self) -> None:
        await self._session.close()


class ReadOnlyViolation(PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class Route:
    method: str
    pattern: str  # регулярное выражение по пути URL

    def matches(self, method: str, path: str) -> bool:
        return method.upper() == self.method and re.fullmatch(self.pattern, path) is not None


class ReadOnlyGuard:
    def __init__(self, routes: list[Route]) -> None:
        self._routes = routes

    def check(self, method: str, url: str) -> None:
        path = urlsplit(url).path
        if not any(r.matches(method, path) for r in self._routes):
            raise ReadOnlyViolation(f"запрещено (только чтение): {method.upper()} {path}")


@dataclass
class Metrics:
    requests: int = 0
    errors: int = 0
    rate_limited: int = 0
    retries: int = 0
    total_latency_s: float = 0.0
    by_status: dict[int, int] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        avg = self.total_latency_s / self.requests if self.requests else 0.0
        return {
            "requests": self.requests,
            "errors": self.errors,
            "rate_limited": self.rate_limited,
            "retries": self.retries,
            "avg_latency_s": round(avg, 3),
            "by_status": dict(self.by_status),
        }


class Throttle:
    """Не чаще одного запроса за `min_interval` секунд (D-008)."""

    def __init__(
        self,
        min_interval: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._min = min_interval
        self._clock = clock
        self._sleep = sleep
        self._next = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = self._clock()
            if now < self._next:
                await self._sleep(self._next - now)
                now = self._next
            self._next = now + self._min

    def push_back(self, seconds: float) -> None:
        """После 429: следующий запрос не раньше, чем через `seconds`."""
        self._next = max(self._next, self._clock() + seconds)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    base_s: float = 2.0
    max_s: float = 300.0
    retry_statuses: frozenset[int] = RETRY_STATUSES

    def delay(self, attempt: int, retry_after: str | None, rng: random.Random) -> float:
        if retry_after is not None:
            try:
                return min(max(float(retry_after), 1.0), self.max_s)
            except ValueError:
                pass
        backoff = min(self.base_s * 2**attempt, self.max_s)
        return backoff * (0.5 + rng.random() / 2)  # jitter 50–100%


class HttpError(MarketError):
    def __init__(self, status: int, url: str) -> None:
        super().__init__(f"HTTP {status} {urlsplit(url).path}")
        self.status = status


class MarketHttp:
    def __init__(
        self,
        market: str,
        base_url: str,
        transport: Transport,
        guard: ReadOnlyGuard,
        *,
        headers: Mapping[str, str] | None = None,
        throttle: Throttle,
        retry: RetryPolicy | None = None,
        timeout_s: float = 10.0,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self.market = market
        self.base_url = base_url.rstrip("/") + "/"
        self._transport = transport
        self._guard = guard
        self._headers = dict(headers or {})
        self._throttle = throttle
        self._retry = retry or RetryPolicy()
        self._timeout = timeout_s
        self._sleep = sleep
        self._rng = rng or random.Random()  # noqa: S311 — jitter, не криптография
        self.metrics = Metrics()

    def url(self, path: str) -> str:
        return path if path.startswith("http") else self.base_url + path.lstrip("/")

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        headers: Mapping[str, str] | None = None,
        ok_statuses: frozenset[int] = frozenset({200}),
    ) -> Response:
        url = self.url(path)
        self._guard.check(method, url)
        merged = self._headers | dict(headers or {})
        last: Response | None = None
        for attempt in range(self._retry.attempts):
            await self._throttle.wait()
            started = time.monotonic()
            self.metrics.requests += 1
            try:
                resp = await self._transport.request(
                    method,
                    url,
                    params=params,
                    json_body=json_body,
                    headers=merged,
                    timeout=self._timeout,
                )
            except (TimeoutError, OSError) as exc:
                self.metrics.errors += 1
                log.warning("%s %s %s: сеть: %s", self.market, method, path, mask_secrets(str(exc)))
                if attempt + 1 >= self._retry.attempts:
                    raise MarketError(f"сеть: {urlsplit(url).path}") from exc
                self.metrics.retries += 1
                await self._sleep(self._retry.delay(attempt, None, self._rng))
                continue
            finally:
                self.metrics.total_latency_s += time.monotonic() - started
            self.metrics.by_status[resp.status] = self.metrics.by_status.get(resp.status, 0) + 1
            if resp.status in ok_statuses:
                return resp
            last = resp
            self.metrics.errors += 1
            if resp.status not in self._retry.retry_statuses:
                break
            retry_after = resp.headers.get("retry-after")
            delay = self._retry.delay(attempt, retry_after, self._rng)
            if resp.status == 429:
                self.metrics.rate_limited += 1
                self._throttle.push_back(delay)
            if attempt + 1 >= self._retry.attempts:
                break
            self.metrics.retries += 1
            log.info(
                "%s %s %s: HTTP %s, пауза %.1f с", self.market, method, path, resp.status, delay
            )
            await self._sleep(delay)
        assert last is not None  # noqa: S101
        raise HttpError(last.status, url)

    async def get_json(self, path: str, **kw: Any) -> Any:
        return (await self.request("GET", path, **kw)).json()

    async def post_json(self, path: str, body: Any, **kw: Any) -> Any:
        return (await self.request("POST", path, json_body=body, **kw)).json()

    async def aclose(self) -> None:
        await self._transport.aclose()
