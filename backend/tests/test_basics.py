import logging
import os
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.security import SecretMaskingFilter, is_private_file, mask_secrets
from app.settings import Settings
from app.timeutil import ensure_utc, from_unix, parse_iso, utcnow


def test_dry_run_default_true(monkeypatch):
    monkeypatch.delenv("DRY_RUN", raising=False)
    assert Settings(_env_file=None).dry_run is True


def test_dry_run_false_is_rejected(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    with pytest.raises(ValidationError, match="DRY_RUN=false запрещён"):
        Settings(_env_file=None)


def test_secrets_not_in_repr(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123456789:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    monkeypatch.setenv("TG_API_HASH", "0123456789abcdef0123456789abcdef")
    s = Settings(_env_file=None)
    text = repr(s)
    assert "AAAAAAAA" not in text
    assert "0123456789abcdef" not in text


def test_budget_lower_bounds(monkeypatch):
    monkeypatch.setenv("MARKET_MIN_INTERVAL_S", "0.1")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_utc_helpers():
    assert utcnow().tzinfo is UTC
    assert from_unix(0) == datetime(1970, 1, 1, tzinfo=UTC)
    assert parse_iso("2026-11-09T10:00:00Z") == datetime(2026, 11, 9, 10, tzinfo=UTC)
    msk = timezone(timedelta(hours=3))
    assert ensure_utc(datetime(2026, 11, 9, 13, tzinfo=msk)) == datetime(
        2026, 11, 9, 10, tzinfo=UTC
    )
    with pytest.raises(ValueError):
        parse_iso("2026-11-09T10:00:00")


@pytest.mark.parametrize(
    ("raw", "must_not_contain"),
    [
        ("Authorization: tma query_id=AAH&user=%7B%22id%22&hash=deadbeef", "deadbeef"),
        ('{"authData": "query_id=AAHxyz&hash=abc123"}', "abc123"),
        ('{"user_auth": "query_id=AAHsecret"}', "AAHsecret"),
        ("token 123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789", "ABCdefGHI"),
        ("Cookie: access_token=7f9c2ba4e88f827d61604550", "7f9c2ba4"),
        ('{"wtf": "U2FsdGVkX19abcdef"}', "U2FsdGVkX19"),
    ],
)
def test_mask_secrets(raw, must_not_contain):
    assert must_not_contain not in mask_secrets(raw)


def test_logging_filter_masks():
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "auth %s", ("hash=topsecret",), None)
    SecretMaskingFilter().filter(record)
    assert "topsecret" not in record.getMessage()


def test_is_private_file(tmp_path):
    f = tmp_path / "s.session"
    f.write_text("x")
    os.chmod(f, 0o600)
    assert is_private_file(f)
    os.chmod(f, 0o644)
    assert not is_private_file(f)
