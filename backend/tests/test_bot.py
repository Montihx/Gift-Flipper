"""Тесты бота и конвейера watch (PLAN 5.x). Telegram и маркеты — подделки."""

from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app.bot.handlers import BUY_DISABLED, panic
from app.bot.keyboards import AlertCb, control_keyboard, deal_keyboard
from app.bot.notifier import Notifier
from app.bot.texts import format_deal, format_sold
from app.db import make_sessionmaker
from app.engine.pipeline import Pipeline
from app.markets.mock import MockClient
from app.models import Alert, Base, Preset
from app.pricing.deal import evaluate
from app.rules import repo
from app.rules.filters import DealFilter
from app.rules.match import Match, PresetRule
from tests.factories import NOW, listing, sale

TON = 1_000_000_000
CHAT = 100


def make_deal(price=3, listing_id="t"):
    t = listing(listing_id, price, model="Watcher", backdrop="Black", url="https://t.me/x")
    book = [t] + [
        listing(i, p, model="Watcher", backdrop="Black")
        for i, p in (("a", "4.0"), ("b", "4.1"), ("c", "4.3"))
    ]
    return evaluate(t, {"portals": book}, [], NOW)


RULE = PresetRule(1, "Дешёвые <Watcher>", 0, True, "watch", DealFilter())
MATCH = Match(RULE, "watch")


class FakeApi:
    def __init__(self):
        self.sent, self.edits, self._next = [], [], 500

    async def send(self, chat_id, text, markup):
        self._next += 1
        self.sent.append((chat_id, text, markup))
        return self._next

    async def edit(self, chat_id, message_id, text, markup):
        self.edits.append((chat_id, message_id, text, markup))


@pytest.fixture
async def sessions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield make_sessionmaker(engine)
    await engine.dispose()


@pytest.fixture
def api():
    return FakeApi()


@pytest.fixture
def notifier(api, sessions):
    return Notifier(api, sessions, "https://app.example")


# --- тексты и кнопки ---------------------------------------------------------------


def test_format_deal_contents():
    text = format_deal(make_deal(), RULE.name)
    assert "Evil Eye #42</b> · Portals" in text
    assert "Цена: <b>3.00 TON</b>" in text
    assert "Флор: 4.00 TON (модель+фон, доверие среднее, 3 шт.)" in text
    assert "Ниже флора: 25.0%" in text
    assert "~0.69 TON" in text and "оценка, комиссии не проверены" in text
    assert "Дешёвые &lt;Watcher&gt;" in text  # HTML экранирован


def test_format_sold():
    assert format_sold("🟢 X", 2 * TON).startswith("🔴 <b>ПРОДАНО</b> за 2.00 TON\nX")


def _buttons(kb):
    return [b for row in kb.inline_keyboard for b in row]


def test_deal_keyboard_has_no_buy_in_watch():
    texts = [b.text for b in _buttons(deal_keyboard(7, "https://t.me/x", "https://app", "watch"))]
    assert texts == ["Пропустить", "Открыть на маркете", "Открыть в приложении"]
    confirm = _buttons(deal_keyboard(7, None, None, "confirm"))
    assert confirm[0].text == "Купить"
    assert AlertCb.unpack(confirm[0].callback_data) == AlertCb(action="buy", alert_id=7)


def test_control_keyboard():
    texts = [b.text for b in _buttons(control_keyboard(False, "https://app"))]
    assert texts == ["Открыть приложение", "⏸ Пауза", "🛑 Panic", "Итог дня"]
    assert _buttons(control_keyboard(True, None))[0].text == "▶️ Продолжить"


def test_buy_message_mentions_disabled():
    assert "выключены" in BUY_DISABLED


# --- Notifier ---------------------------------------------------------------------


async def test_notify_then_price_change_then_sold(notifier, api, sessions):
    a = await notifier.notify(CHAT, make_deal(3), MATCH)
    assert a is not None and a.message_id == 501 and len(api.sent) == 1
    assert await notifier.notify(CHAT, make_deal(3), MATCH) is None  # без изменений
    b = await notifier.notify(CHAT, make_deal("2.8"), MATCH)
    assert b is not None and b.id == a.id and len(api.sent) == 1  # правка, не новое
    assert api.edits[-1][2].startswith("🟡 Цена снизилась: 3.00 → <b>2.80 TON</b>")
    assert await notifier.mark_sold("portals", "t", 2_800_000_000) == 1
    chat, msg, text, markup = api.edits[-1]
    assert (chat, msg) == (CHAT, 501) and text.startswith("🔴 <b>ПРОДАНО</b> за 2.80 TON")
    assert markup.inline_keyboard == []
    assert await notifier.mark_sold("portals", "t") == 0  # уже закрыто
    assert await notifier.notify(CHAT, make_deal("2.5"), MATCH) is None


async def test_pause_and_panic_block_new(notifier, api, sessions):
    await notifier.set_state(CHAT, paused=True)
    assert await notifier.notify(CHAT, make_deal(), MATCH) is None
    await notifier.set_state(CHAT, paused=False)
    async with sessions() as s:
        await repo.create_preset(s, CHAT, "auto", DealFilter(), mode="auto")
        await s.commit()
    await panic(notifier, sessions, CHAT)
    st = await notifier.state(CHAT)
    assert st.panic and st.paused
    async with sessions() as s:
        modes = (await s.execute(select(Preset.mode))).scalars().all()
    assert modes == ["watch"]
    assert await notifier.notify(CHAT, make_deal(), MATCH) is None
    assert api.sent == []


async def test_skip_and_summary(notifier, api):
    a = await notifier.notify(CHAT, make_deal(3, "t1"), MATCH)
    await notifier.notify(CHAT, make_deal(3, "t2"), MATCH)
    await notifier.notify(CHAT, make_deal(3, "t3"), MATCH)
    assert await notifier.skip(CHAT, a.id) is True
    assert await notifier.skip(CHAT, a.id) is False
    assert await notifier.skip(999, a.id) is False
    await notifier.mark_sold("portals", "t2")
    s = await notifier.summary(CHAT, NOW + timedelta(days=3650))
    assert s.alerts == 0  # окно 24 ч от «будущего» — пусто
    s = await notifier.summary(CHAT)
    assert (s.alerts, s.sold, s.skipped, s.best_profit_nano) == (3, 1, 1, 690_500_000)
    assert "Покупок: 0" in s.text()


# --- Pipeline ------------------------------------------------------------------------


class FakeNotifier:
    def __init__(self):
        self.notified, self.sold = [], []

    async def notify(self, chat_id, deal, match):
        self.notified.append((chat_id, deal.listing.listing_id, match.preset.id))
        return object()

    async def mark_sold(self, market, listing_id, price_nano=None):
        self.sold.append((market, listing_id))
        return 1


async def test_pipeline_cycle():
    target = listing("t", 3, model="Watcher", backdrop="Black")
    book = [target] + [
        listing(i, p, model="Watcher", backdrop="Black")
        for i, p in (("a", "4.0"), ("b", "4.1"), ("c", "4.3"))
    ]
    portals = MockClient("portals", listings=book)
    tonnel = MockClient("tonnel", sales=[sale("s1", 5, listing_id="99", occurred_at=NOW)])
    fn = FakeNotifier()
    p = Pipeline([portals, tonnel], fn, CHAT)
    rules = [PresetRule(1, "скидка 20%", 0, True, "auto", DealFilter(min_discount_bps=2000))]
    r1 = await p.run_cycle(rules, NOW)
    assert (r1.listings, r1.evaluated, r1.notified, r1.sold_marked) == (4, 4, 1, 1)
    assert fn.notified == [(CHAT, "t", 1)]
    assert fn.sold == [("tonnel", "99")]
    r2 = await p.run_cycle(rules, NOW)  # всё уже видели
    assert (r2.evaluated, r2.notified, r2.sold_marked) == (0, 0, 0)


async def test_pipeline_survives_market_error():
    from app.markets.base import MarketError

    bad = MockClient("mrkt", fail_with=MarketError("down"))
    ok = MockClient("portals", listings=[listing("x", 3)])
    r = await Pipeline([bad, ok], FakeNotifier(), CHAT).run_cycle([], NOW)
    assert r.listings == 1 and any("mrkt" in e for e in r.errors)


async def test_alert_unique_per_chat_listing(sessions, api):
    n = Notifier(api, sessions)
    await n.notify(CHAT, make_deal(), MATCH)
    await n.notify(CHAT + 1, make_deal(), MATCH)
    async with sessions() as s:
        assert len((await s.execute(select(Alert))).scalars().all()) == 2
