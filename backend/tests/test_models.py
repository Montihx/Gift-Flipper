from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.db import make_sessionmaker
from app.models import Base, Listing, Sale

NOW = datetime(2026, 11, 9, 10, tzinfo=UTC)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with make_sessionmaker(engine)() as s:
        yield s
    await engine.dispose()


def _listing(**kw):
    base = {
        "market": "portals",
        "listing_id": "abc",
        "collection": "Plush Pepe",
        "model": "Cozy",
        "backdrop": "Black",
        "price_nano": 44_000_000_000,
        "first_seen_at": NOW,
        "last_seen_at": NOW,
    }
    return Listing(**(base | kw))


async def test_listing_roundtrip(session):
    session.add(_listing())
    await session.commit()
    row = (await session.execute(select(Listing))).scalar_one()
    assert row.price_nano == 44_000_000_000
    assert row.status == "listed"


async def test_listing_unique_per_market(session):
    session.add_all([_listing(), _listing()])
    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.parametrize("bad", [{"market": "getgems"}, {"price_nano": 0}])
async def test_listing_checks(session, bad):
    session.add(_listing(**bad))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_sale_unique_event(session):
    kw = {
        "market": "tonnel",
        "event_id": "e1",
        "collection": "Plush Pepe",
        "price_nano": 3_570_000_000,
        "occurred_at": NOW,
    }
    session.add_all([Sale(**kw), Sale(**kw)])
    with pytest.raises(IntegrityError):
        await session.commit()
