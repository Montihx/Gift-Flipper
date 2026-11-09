"""Пресеты фильтров (PLAN 4.2). Фильтр — JSON по схеме `rules.filters.DealFilter`."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, CheckConstraint, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.market import PK


class Preset(Base):
    __tablename__ = "presets"
    __table_args__ = (
        CheckConstraint("mode IN ('watch', 'confirm', 'auto')", name="mode"),
        Index("ix_presets_owner", "owner_chat_id"),
    )

    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    owner_chat_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    mode: Mapped[str] = mapped_column(String(8), default="watch")
    filter: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
