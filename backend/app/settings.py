"""Настройки приложения из окружения и `.env`.

Секреты хранятся как `SecretStr`: в repr/логах они не раскрываются (AGENTS.md §4.2).
`DRY_RUN` по умолчанию `true`, и выключить его до Этапа 7 нельзя (D-003, D-009).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

# Переключатель живой торговли. Меняется только отдельным PR после
# «разрешаю этап 7» от владельца и проверенной таблицы комиссий.
LIVE_TRADING_ALLOWED = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Безопасность
    dry_run: bool = True

    # Хранилища
    database_url: str = "postgresql+asyncpg://giftflipper:giftflipper@localhost:5432/giftflipper"
    redis_url: str = "redis://localhost:6379/0"
    data_dir: Path = PROJECT_DIR / "data"

    # Telegram (секреты — только из .env)
    bot_token: SecretStr | None = None
    owner_chat_id: int | None = None
    tg_api_id: int | None = None
    tg_api_hash: SecretStr | None = None
    tg_session_name: str = "owner"

    # Бюджет запросов к маркетам (D-008)
    market_min_interval_s: float = Field(default=1.0, ge=0.5)
    listings_poll_interval_s: float = Field(default=5.0, ge=1.0)
    request_timeout_s: float = Field(default=10.0, gt=0)
    backoff_base_s: float = Field(default=2.0, gt=0)
    backoff_max_s: float = Field(default=300.0, gt=0)

    log_level: str = "INFO"

    @field_validator("dry_run")
    @classmethod
    def _dry_run_locked(cls, value: bool) -> bool:
        if not value and not LIVE_TRADING_ALLOWED:
            raise ValueError(
                "DRY_RUN=false запрещён: живая торговля не разрешена (D-003, D-009, Этап 7)"
            )
        return value

    @property
    def tg_session_path(self) -> Path:
        return self.data_dir / f"{self.tg_session_name}.session"


@lru_cache
def get_settings() -> Settings:
    return Settings()
