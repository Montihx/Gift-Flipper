"""Время: только UTC с tz (AGENTS.md §5)."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def from_unix(seconds: int | float) -> datetime:
    return datetime.fromtimestamp(seconds, UTC)


def ensure_utc(value: datetime) -> datetime:
    """Наивное время запрещено: его происхождение неизвестно."""
    if value.tzinfo is None:
        raise ValueError("naive datetime запрещён, нужен tz")
    return value.astimezone(UTC)


def parse_iso(value: str) -> datetime:
    """ISO 8601; `Z` и смещения допустимы, наивные строки — ошибка."""
    return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
