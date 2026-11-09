"""Отправленные уведомления (для «ПРОДАНО» и правки цены) и состояние бота (PLAN 5.2–5.3)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.market import PK


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint("chat_id", "market", "listing_id", name="uq_alerts_chat_listing"),
        CheckConstraint("status IN ('active', 'sold', 'skipped', 'gone')", name="status"),
        Index("ix_alerts_listing", "market", "listing_id"),
    )

    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[int] = mapped_column(BigInteger)
    market: Mapped[str] = mapped_column(String(16))
    listing_id: Mapped[str] = mapped_column(String(64))
    preset_id: Mapped[int | None] = mapped_column(BigInteger)
    price_nano: Mapped[int] = mapped_column(BigInteger)  # цена в последнем тексте
    profit_nano: Mapped[int | None] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(String(4096))
    status: Mapped[str] = mapped_column(String(16), default="active")
    sent_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class BotState(Base):
    """Пауза и Panic на чат. Panic — всё в watch и стоп исполнения (AGENTS.md §8)."""

    __tablename__ = "bot_state"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    panic: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime]
