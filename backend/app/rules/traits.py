"""Особые признаки подарка (PLAN 4.1, SUMMARY.md §2).

- «Красивый» номер: мало разных цифр — `len(set(str(n))) ≤ N` (из кода topcvetok
  special_traits.py:24-36, по умолчанию N=3).
- Монохром: внешний сигнал Clue `GET https://app.clue.tg/api/mono/resolve?url=<slug-n>`
  → `{"score": 0..100}`, порог 80 (из кода topcvetok). Клиент Clue — позже (Этап 5);
  здесь только правило по уже полученному score.
"""

from __future__ import annotations

import re

MONOCHROME_MIN_SCORE = 80


def distinct_digits(number: int) -> int:
    return len(set(str(abs(number))))


def is_beautiful(number: int | None, max_distinct: int = 3) -> bool:
    return number is not None and distinct_digits(number) <= max_distinct


def is_monochrome(score: int | None, threshold: int = MONOCHROME_MIN_SCORE) -> bool:
    return score is not None and score >= threshold


def clue_slug(collection: str, number: int) -> str:
    """`"Evil Eye", 42` → `"evileye-42"` (формат из кода topcvetok special_traits.py:15-21)."""
    return f"{re.sub(r'[^0-9a-z]', '', collection.casefold())}-{number}"
