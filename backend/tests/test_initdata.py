"""Проверка initData Mini App (PLAN 6.1). Алгоритм — документация Telegram Bot API:
secret = HMAC_SHA256(key="WebAppData", msg=bot_token);
hash = hex(HMAC_SHA256(key=secret, msg=data_check_string)), где data_check_string —
все поля, кроме hash, `k=v`, отсортированные по ключу, через `\\n`."""

import hashlib
import hmac
import json
from datetime import timedelta
from urllib.parse import urlencode

import pytest

from app.api.auth import InitDataError, verify_init_data
from tests.factories import NOW

TOKEN = "123456789:TEST-token-not-real-aaaaaaaaaaaaaaa"


def sign(fields: dict[str, str], token: str = TOKEN) -> str:
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": h})


def fields(user_id=100, auth_date=None):
    return {
        "query_id": "AAH",
        "user": json.dumps({"id": user_id, "first_name": "Владелец"}, ensure_ascii=False),
        "auth_date": str(int((auth_date or NOW).timestamp())),
    }


def test_valid():
    u = verify_init_data(sign(fields()), TOKEN, now=NOW)
    assert u.id == 100 and u.first_name == "Владелец"


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (lambda: sign(fields(), token="999:other-token-xxxxxxxxxxxxxxxxxxxxxxxx"), "подпись"),
        (lambda: sign(fields()).replace("AAH", "AAX"), "подпись"),
        (lambda: urlencode(fields()), "hash"),
        (lambda: sign(fields(auth_date=NOW - timedelta(hours=25))), "устарел"),
        (lambda: sign(fields(auth_date=NOW + timedelta(minutes=10))), "будущего"),
        (lambda: sign({"auth_date": str(int(NOW.timestamp()))}), "user"),
    ],
)
def test_invalid(raw, message):
    with pytest.raises(InitDataError, match=message):
        verify_init_data(raw(), TOKEN, now=NOW)
