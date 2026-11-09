"""Секреты: маскирование в логах и проверка прав файлов (AGENTS.md §4.2)."""

from __future__ import annotations

import logging
import re
import stat
from pathlib import Path

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Authorization: tma <initData> / Bearer <token> / сырой токен
    (
        re.compile(r"(?i)(authorization[\"']?\s*[:=]\s*[\"']?)(tma\s+|bearer\s+)?[^\s\"',}]+"),
        r"\1\2***",
    ),
    # initData и его поля: query_id=…&user=…&auth_date=…&hash=…
    (re.compile(r"(?i)\b(hash|signature|query_id|user|tgWebAppData)=([^&\s\"']+)"), r"\1=***"),
    # поля тел запросов с авторизацией
    (
        re.compile(
            r"(?i)([\"']?(?:authData|user_auth|initData|access_token|token|api_hash|wtf)"
            r"[\"']?\s*[:=]\s*[\"']?)([^\"'&\s,}]{4,})"
        ),
        r"\1***",
    ),
    # токен бота: 123456:ABC...
    (re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"), "***:***"),
]


def mask_secrets(text: str) -> str:
    for pattern, repl in _PATTERNS:
        text = pattern.sub(repl, text)
    return text


class SecretMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = mask_secrets(record.getMessage())
        record.args = ()
        return True


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.addFilter(SecretMaskingFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)


def is_private_file(path: Path) -> bool:
    """True, если файл доступен только владельцу (0o600 или строже)."""
    mode = path.stat().st_mode
    return stat.S_IMODE(mode) & 0o077 == 0


def ensure_private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path
