"""Тесты правил, фильтров, пресетов (PLAN 4.4)."""

from datetime import timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import create_async_engine

from app.db import make_sessionmaker
from app.models import Base
from app.pricing.deal import evaluate
from app.rules import repo
from app.rules.filters import DealFilter
from app.rules.match import Deduper, PresetRule, effective_mode, match_presets, reasons_rejected
from app.rules.traits import clue_slug, distinct_digits, is_beautiful, is_monochrome
from tests.factories import NOW, listing

TON = 1_000_000_000


def book(target):
    return {
        "portals": [
            target,
            listing("a", "4.0", model="Watcher", backdrop="Black"),
            listing("b", "4.1", model="Watcher", backdrop="Black"),
            listing("c", "4.3", model="Watcher", backdrop="Black"),
        ],
    }


def deal(**kw):
    t = listing(
        "t",
        kw.pop("price", 3),
        model="Watcher",
        backdrop="Black",
        model_rarity_pm=15,
        backdrop_rarity_pm=20,
        **kw,
    )
    return evaluate(t, book(t), [], NOW)


# --- traits -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("number", "distinct", "beautiful3"),
    [
        (7, 1, True),
        (777, 1, True),
        (1000, 2, True),
        (1212, 2, True),
        (123, 3, True),
        (1234, 4, False),
        (90817, 5, False),
    ],
)
def test_beautiful_numbers(number, distinct, beautiful3):
    assert distinct_digits(number) == distinct
    assert is_beautiful(number, 3) is beautiful3


def test_monochrome_and_slug():
    assert is_monochrome(80) and not is_monochrome(79) and not is_monochrome(None)
    assert clue_slug("Evil Eye", 42) == "evileye-42"
    assert clue_slug("Jack-in-the-Box", 7) == "jackinthebox-7"


# --- filter schema ------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        {"min_price_nano": 5, "max_price_nano": 4},
        {"number": {"min": 10, "max": 5}},
        {"markets": ["getgems"]},
        {"unknown_field": 1},
        {"min_discount_bps": 20_000},
        {"min_confidence": "ultra"},
    ],
)
def test_filter_validation(bad):
    with pytest.raises(ValidationError):
        DealFilter.model_validate(bad)


# --- reasons_rejected: табличный тест -------------------------------------------
# сделка по умолчанию: Portals, 3 TON, флор 4.0 (med, 3 сопоставимых), скидка 25%,
# прибыль 3.6905 − 3 = 0.6905 TON, ROI 2301 bps, номер 42, редкость модели 1.5%


@pytest.mark.parametrize(
    ("flt", "reasons"),
    [
        ({}, []),
        ({"markets": ["mrkt"]}, ["market"]),
        ({"collections": ["evil eye"]}, []),  # нормализация названий
        ({"collections": ["Plush Pepe"]}, ["collection"]),
        ({"models": ["watcher"], "backdrops": ["Black"]}, []),
        ({"symbols": ["Star"]}, ["symbol"]),
        ({"max_model_rarity_pm": 15}, []),
        ({"max_model_rarity_pm": 10}, ["model_rarity"]),
        ({"max_symbol_rarity_pm": 50}, ["symbol_rarity"]),  # редкость символа неизвестна
        ({"number": {"min": 1, "max": 100}}, []),
        ({"number": {"max": 10}}, ["number_range"]),
        ({"number": {"max_distinct_digits": 1}}, ["number_digits"]),
        ({"monochrome_only": True}, ["monochrome"]),
        ({"max_price_nano": 3 * TON}, []),
        ({"max_price_nano": 3 * TON - 1}, ["price_max"]),
        ({"min_price_nano": 5 * TON}, ["price_min"]),
        ({"min_discount_bps": 2500}, []),
        ({"min_discount_bps": 2501}, ["discount"]),
        ({"min_profit_nano": 690_500_000}, []),
        ({"min_profit_nano": 690_500_001}, ["profit"]),
        ({"min_roi_bps": 2301}, []),
        ({"min_roi_bps": 2302}, ["roi"]),
        ({"min_confidence": "high"}, ["confidence"]),
        ({"min_comparables": 4}, ["comparables"]),
    ],
)
def test_reasons_rejected(flt, reasons):
    d = deal()
    assert d.profit_nano == 690_500_000 and d.roi_bps == 2301  # опорные числа
    assert reasons_rejected(d, DealFilter.model_validate(flt)) == reasons


def test_monochrome_with_score():
    f = DealFilter(monochrome_only=True)
    assert reasons_rejected(deal(), f, monochrome_score=85) == []


def test_exclusions():
    locked = deal(locked_until=NOW + timedelta(hours=1))
    assert "locked" in reasons_rejected(locked, DealFilter())
    f = DealFilter.model_validate({"exclude": {"locked": False}})
    assert reasons_rejected(locked, f) == []
    cheap = deal(price="0.5")
    assert "too_good" in reasons_rejected(cheap, DealFilter())


# --- presets matching ----------------------------------------------------------


def rule(i, prio=0, enabled=True, mode="watch", **flt):
    return PresetRule(i, f"p{i}", prio, enabled, mode, DealFilter.model_validate(flt))


def test_match_presets_priority_and_enabled():
    d = deal()
    rules = [
        rule(1, prio=1),
        rule(2, prio=5, mode="auto"),
        rule(3, prio=9, enabled=False),
        rule(4, prio=9, markets=["tonnel"]),
        rule(5, prio=5),
    ]
    got = match_presets(d, rules)
    assert [m.preset.id for m in got] == [2, 5, 1]
    assert all(m.effective_mode == "watch" for m in got)  # торговля не разрешена


@pytest.mark.parametrize("mode", ["watch", "confirm", "auto"])
def test_effective_mode_is_watch(mode):
    assert effective_mode(mode, deal()) == "watch"


def test_deduper_only_lower_price():
    dd = Deduper()
    assert dd.should_notify(1, deal(price=3))
    assert not dd.should_notify(1, deal(price=3))
    assert not dd.should_notify(1, deal(price="3.5"))
    assert dd.should_notify(1, deal(price="2.9"))
    assert dd.should_notify(2, deal(price=3))  # другой чат


# --- CRUD ------------------------------------------------------------------------


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with make_sessionmaker(engine)() as s:
        yield s
    await engine.dispose()


async def test_preset_crud(session):
    p = await repo.create_preset(
        session,
        100,
        "Дешёвые Watcher",
        DealFilter(models=["Watcher"], min_discount_bps=1500),
        priority=2,
    )
    await repo.create_preset(session, 100, "Другой", DealFilter(), priority=5)
    await repo.create_preset(session, 200, "Чужой", DealFilter())
    names = [x.name for x in await repo.list_presets(session, 100)]
    assert names == ["Другой", "Дешёвые Watcher"]
    assert await repo.get_preset(session, 200, p.id) is None  # чужой пресет не виден
    upd = await repo.update_preset(session, 100, p.id, enabled=False, filter={"markets": ["mrkt"]})
    assert upd is not None and upd.enabled is False and upd.filter["markets"] == ["mrkt"]
    with pytest.raises(ValidationError):
        await repo.update_preset(session, 100, p.id, filter={"markets": ["nope"]})
    with pytest.raises(ValueError):
        await repo.update_preset(session, 100, p.id, id=999)
    rules = await repo.active_rules(session, 100)
    assert [r.name for r in rules] == ["Другой"]
    assert await repo.delete_preset(session, 100, p.id) is True
    assert await repo.delete_preset(session, 100, p.id) is False
