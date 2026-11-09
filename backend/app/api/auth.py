"""Проверка `initData` Mini App на бэкенде (PLAN 6.1).

Алгоритм — из документации Telegram Bot API («Validating data received via the Mini App»):
secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token);
hash = hex(HMAC_SHA256(key=secret_key, msg=data_check_string)),
data_check_string — все поля кроме `hash`, `key=value`, по алфавиту, через `\\n`.
Плюс свежесть `auth_date` (по умолчанию 24 ч). initData не логируется.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import parse_qsl

from app.timeutil import from_unix, utcnow


class InitDataError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TgUser:
    id: int
    first_name: str | None
    username: str | None


def verify_init_data(
    raw: str,
    bot_token: str,
    *,
    max_age: timedelta = timedelta(hours=24),
    now: datetime | None = None,
) -> TgUser:
    pairs = dict(parse_qsl(raw, keep_blank_values=True, strict_parsing=False))
    received = pairs.pop("hash", None)
    if not received:
        raise InitDataError("нет hash")
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise InitDataError("неверная подпись")
    try:
        auth_date = from_unix(int(pairs["auth_date"]))
    except (KeyError, ValueError) as exc:
        raise InitDataError("нет auth_date") from exc
    now = now or utcnow()
    if auth_date > now + timedelta(minutes=1):
        raise InitDataError("auth_date из будущего")
    if now - auth_date > max_age:
        raise InitDataError("initData устарел")
    try:
        user = json.loads(pairs["user"])
        return TgUser(int(user["id"]), user.get("first_name"), user.get("username"))
    except (KeyError, ValueError, TypeError) as exc:
        raise InitDataError("нет user") from exc
