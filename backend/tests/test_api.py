"""Тесты API Mini App (PLAN 6.1–6.4). Telegram не нужен: initData подписывается в тесте."""

from datetime import timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import MODES_LOCKED, create_app
from app.bot.notifier import Notifier
from app.db import make_sessionmaker
from app.engine.store import save_sales
from app.models import Base
from app.rules.match import Match
from app.settings import Settings
from app.timeutil import utcnow
from tests.factories import sale
from tests.test_bot import MATCH, FakeApi, make_deal
from tests.test_initdata import TOKEN, fields, sign

OWNER = 100


@pytest.fixture
async def env(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessions = make_sessionmaker(engine)
    settings = Settings(_env_file=None, bot_token=TOKEN, owner_chat_id=OWNER)
    app = create_app(settings, sessions)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        yield client, sessions
    await engine.dispose()


def auth(user_id=OWNER):
    return {"Authorization": "tma " + sign(fields(user_id=user_id, auth_date=utcnow()))}


@pytest.mark.parametrize(
    ("headers", "status"),
    [
        ({}, 401),
        ({"Authorization": "Bearer x"}, 401),
        ({"Authorization": "tma hash=00&auth_date=1"}, 401),
        ("other_user", 403),
        ("owner", 200),
    ],
)
async def test_auth(env, headers, status):
    client, _ = env
    if headers == "other_user":
        headers = auth(555)
    elif headers == "owner":
        headers = auth()
    r = await client.get("/api/me", headers=headers)
    assert r.status_code == status


async def test_me_reports_safety(env):
    client, _ = env
    body = (await client.get("/api/me", headers=auth())).json()
    assert body["dry_run"] is True and body["live_trading_allowed"] is False
    assert body["fees"]["tonnel"]["buy_bps"] == 1000
    assert all(not f["verified"] for f in body["fees"].values())


async def test_presets_crud_and_mode_lock(env):
    client, _ = env
    h = auth()
    r = await client.post(
        "/api/presets",
        headers=h,
        json={
            "name": "Watcher −15%",
            "priority": 3,
            "filter": {"models": ["Watcher"], "min_discount_bps": 1500},
        },
    )
    assert r.status_code == 201
    pid = r.json()["id"]
    assert r.json()["mode"] == "watch"
    r = await client.post("/api/presets", headers=h, json={"name": "auto", "mode": "auto"})
    assert r.status_code == 409 and r.json()["detail"] == MODES_LOCKED
    r = await client.patch(f"/api/presets/{pid}", headers=h, json={"mode": "confirm"})
    assert r.status_code == 409
    r = await client.post(
        "/api/presets", headers=h, json={"name": "x", "filter": {"markets": ["x"]}}
    )
    assert r.status_code == 422
    r = await client.patch(
        f"/api/presets/{pid}", headers=h, json={"enabled": False, "filter": {"markets": ["tonnel"]}}
    )
    assert r.status_code == 200 and r.json()["enabled"] is False
    assert r.json()["filter"]["markets"] == ["tonnel"]
    listed = (await client.get("/api/presets", headers=h)).json()
    assert [p["id"] for p in listed] == [pid]
    assert (await client.get("/api/presets", headers=auth(555))).status_code == 403
    assert (await client.delete(f"/api/presets/{pid}", headers=h)).status_code == 204
    assert (await client.delete(f"/api/presets/{pid}", headers=h)).status_code == 404


async def test_deals_feed_card_and_sales(env):
    client, sessions = env
    n = Notifier(FakeApi(), sessions)
    a = await n.notify(OWNER, make_deal(3, "t1"), MATCH)
    await n.notify(OWNER, make_deal(3, "t2"), Match(MATCH.preset, "watch"))
    await n.notify(999, make_deal(3, "t3"), MATCH)  # чужой чат не виден
    async with sessions() as s:
        await save_sales(
            s,
            [
                sale("s1", "4.2", market="portals", occurred_at=utcnow()),
                sale("s2", "4.4", market="tonnel", occurred_at=utcnow() - timedelta(days=10)),
            ],
        )
        await s.commit()
    h = auth()
    feed = (await client.get("/api/deals", headers=h)).json()
    assert [d["listing_id"] for d in feed] == ["t2", "t1"]
    assert feed[0]["price_ton"] == "3.00" and feed[0]["profit_ton"] == "0.69"
    assert feed[0]["estimate"] is True
    card = (await client.get(f"/api/deals/{a.id}", headers=h)).json()
    deal = card["deal"]
    assert deal["listing"]["collection"] == "Evil Eye"
    assert deal["all_in"] == {"nano": "3000000000", "ton": "3.00"}
    assert deal["options"][0]["floor"]["ton"] == "4.00"
    assert deal["options"][0]["confidence"] == "med"
    sales = (await client.get(f"/api/deals/{a.id}/sales", headers=h)).json()
    assert [x["price_ton"] for x in sales] == ["4.20"]  # продажа 10-дневной давности не входит
    assert (await client.get("/api/deals/99999", headers=h)).status_code == 404


async def test_state_pause_and_panic(env):
    client, _ = env
    h = auth()
    r = await client.post("/api/state", headers=h, json={"paused": True})
    assert r.json() == {"paused": True, "panic": False}
    r = await client.post("/api/state", headers=h, json={"panic": True})
    assert r.json() == {"paused": True, "panic": True}
    r = await client.post("/api/state", headers=h, json={"panic": False})
    assert r.json() == {"paused": False, "panic": False}


async def test_save_sales_idempotent(env):
    _, sessions = env
    async with sessions() as s:
        assert await save_sales(s, [sale("a"), sale("b")]) == 2
        assert await save_sales(s, [sale("a"), sale("c")]) == 1
        await s.commit()
