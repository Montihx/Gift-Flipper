"""Сопоставление названий коллекций между маркетами (PLAN 3.5).

Нормализация — как в morgan-gift-plugins gift-price-compare (из кода): нижний регистр,
без пробелов, `_`, `-`. Плюс явная таблица алиасов: готовой таблицы Portals/MRKT/Tonnel
в источниках нет (SUMMARY.md §2), заполняется по живым каталогам коллекций.
Подстрочное сравнение (как у morgan для MarketApp/Fragment) не используем — даёт ложные
совпадения.
"""

from __future__ import annotations

import re

_STRIP = re.compile(r"[\s_\-'’.]+")

# нормализованное имя на маркете → каноническое нормализованное имя
EXPLICIT_ALIASES: dict[str, str] = {}


def normalize(name: str) -> str:
    key = _STRIP.sub("", name.casefold())
    return EXPLICIT_ALIASES.get(key, key)


def same_collection(a: str, b: str) -> bool:
    return normalize(a) == normalize(b)
