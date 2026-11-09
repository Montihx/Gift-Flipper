"""Наблюдаемые данные маркетов: листинги и продажи."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

MARKETS = ("portals", "mrkt", "tonnel")
# BIGSERIAL в PostgreSQL; в SQLite (тесты) автоинкремент есть только у INTEGER.
PK = BigInteger().with_variant(Integer, "sqlite")
_MARKET_CHECK = "market IN ('portals', 'mrkt', 'tonnel')"


class Listing(Base):
    """Последнее известное состояние объявления. Ключ — (market, listing_id)."""

    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("market", "listing_id", name="uq_listings_market_listing"),
        CheckConstraint(_MARKET_CHECK, name="market"),
        CheckConstraint("price_nano > 0", name="price_positive"),
        Index("ix_listings_lookup", "collection", "model", "backdrop"),
    )

    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(16))
    listing_id: Mapped[str] = mapped_column(String(64))
    collection: Mapped[str] = mapped_column(String(128))
    model: Mapped[str | None] = mapped_column(String(128))
    backdrop: Mapped[str | None] = mapped_column(String(128))
    symbol: Mapped[str | None] = mapped_column(String(128))
    number: Mapped[int | None] = mapped_column(BigInteger)
    price_nano: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default="listed")
    first_seen_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]


class Sale(Base):
    """Совершённая продажа (из ленты/событий маркета). Источник медианы 24 ч."""

    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("market", "event_id", name="uq_sales_market_event"),
        CheckConstraint(_MARKET_CHECK, name="market"),
        CheckConstraint("price_nano > 0", name="price_positive"),
        Index("ix_sales_lookup", "collection", "model", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(16))
    event_id: Mapped[str] = mapped_column(String(96))
    listing_id: Mapped[str | None] = mapped_column(String(64))
    collection: Mapped[str] = mapped_column(String(128))
    model: Mapped[str | None] = mapped_column(String(128))
    backdrop: Mapped[str | None] = mapped_column(String(128))
    symbol: Mapped[str | None] = mapped_column(String(128))
    number: Mapped[int | None] = mapped_column(BigInteger)
    price_nano: Mapped[int] = mapped_column(BigInteger)
    occurred_at: Mapped[datetime]
