"""Табличные тесты оценки (PLAN 3.2–3.6). Числа посчитаны вручную в комментариях."""

from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.pricing.aliases import normalize, same_collection
from app.pricing.deal import evaluate
from app.pricing.fees import DEFAULT_FEES, FeeSchedule
from app.pricing.sales import check_with_sales, matching_sales, median
from app.pricing.tg_value import (
    above_telegram_value,
    fiat_minor_to_nano,
    minor_to_major,
    parse_value_info,
)
from tests.factories import NOW, listing, sale

TON = 1_000_000_000


# --- медиана продаж ------------------------------------------------------------


@pytest.mark.parametrize(
    ("values", "expected"),
    [([5], 5), ([1, 3, 2], 2), ([1, 2, 3, 4], 2), ([4, 5], 4), ([10, 11], 10)],
)
def test_median(values, expected):
    assert median(values) == expected


@pytest.mark.parametrize(
    ("floor", "sales", "resale", "capped"),
    [
        (5 * TON, [], 5 * TON, False),
        (5 * TON, [4 * TON, 6 * TON], 5 * TON, False),  # мало продаж (2 < 3)
        (5 * TON, [4 * TON, 4_500_000_000, 6 * TON], 4_500_000_000, True),
        (5 * TON, [6 * TON, 7 * TON, 8 * TON], 5 * TON, False),  # медиана выше флора
    ],
)
def test_check_with_sales(floor, sales, resale, capped):
    r = check_with_sales(floor, sales)
    assert (r.resale_nano, r.capped_by_sales, r.count) == (resale, capped, len(sales))


def test_matching_sales_window_and_basis():
    t = listing(model="Watcher", backdrop="Black")
    sales = [
        sale("1", 4, model="Watcher", backdrop="Black", occurred_at=NOW - timedelta(hours=1)),
        sale("2", 5, model="Watcher", backdrop="Red", occurred_at=NOW - timedelta(hours=2)),
        sale("3", 6, model="Other", backdrop="Black", occurred_at=NOW - timedelta(hours=3)),
        sale("4", 7, model="Watcher", backdrop="Black", occurred_at=NOW - timedelta(hours=25)),
        sale("5", 8, collection="Plush Pepe", occurred_at=NOW),
    ]
    assert matching_sales(t, sales, "model_backdrop", NOW) == [4 * TON]
    assert matching_sales(t, sales, "model", NOW) == [4 * TON, 5 * TON]
    assert matching_sales(t, sales, "collection", NOW) == [4 * TON, 5 * TON, 6 * TON]


# --- алиасы ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "same"),
    [
        ("Jack-in-the-Box", "jack in the box", True),
        ("Plush Pepe", "plush_pepe", True),
        ("B-Day Candle", "BDay Candle", True),
        ("Evil Eye", "Evil Eyes", False),
    ],
)
def test_same_collection(a, b, same):
    assert same_collection(a, b) is same


def test_normalize():
    assert normalize("  Durov's Cap ") == "durovscap"


# --- оценка Telegram -----------------------------------------------------------


@pytest.mark.parametrize(
    ("amount", "currency", "major"),
    [(12345, "USD", Decimal("123.45")), (500, "JPY", Decimal("500")), (99, "rub", Decimal("0.99"))],
)
def test_minor_to_major(amount, currency, major):
    assert minor_to_major(amount, currency) == major


@pytest.mark.parametrize(
    ("amount", "currency", "rate", "nano"),
    [
        (1500, "USD", Decimal("3"), 5 * TON),  # $15 при $3 за TON = 5 TON
        (100, "USD", Decimal("3"), 333_333_333),  # округление вниз
        (30000, "RUB", Decimal("250"), 1_200_000_000),  # 300 ₽ / 250 = 1.2 TON
    ],
)
def test_fiat_to_nano(amount, currency, rate, nano):
    assert fiat_minor_to_nano(amount, currency, rate) == nano


def test_above_telegram_value():
    obj = SimpleNamespace(
        currency="USD",
        value=1500,
        average_price=1500,
        last_sale_price=1200,
        floor_price=None,
        listed_count=4,
        last_sale_date=None,
    )
    tg = parse_value_info(obj)
    # средняя 5 TON, последняя 4 TON при курсе $3
    assert above_telegram_value(5_100_000_000, tg, Decimal("3")) is True
    assert above_telegram_value(5 * TON, tg, Decimal("3")) is False
    no_data = parse_value_info(SimpleNamespace(currency="USD", value=1))
    assert above_telegram_value(TON, no_data, Decimal("3")) is None


# --- Deal ------------------------------------------------------------------------


def books():
    return {
        "portals": [
            listing("t", 3, model="Watcher", backdrop="Black"),
            listing("a", "4.0", model="Watcher", backdrop="Black"),
            listing("b", "4.1", model="Watcher", backdrop="Black"),
            listing("c", "4.3", model="Watcher", backdrop="Black"),
        ],
        "tonnel": [
            listing("x", "5.0", market="tonnel", model="Watcher", backdrop="Black"),
            listing("y", "5.1", market="tonnel", model="Watcher", backdrop="Black"),
            listing("z", "5.2", market="tonnel", model="Watcher", backdrop="Black"),
        ],
        "mrkt": [],
    }


def test_deal_cross_market_best_resale():
    target = books()["portals"][0]
    d = evaluate(target, books(), [], NOW)
    # all-in Portals: 3 TON (0%)
    assert d.all_in_nano == 3 * TON
    # Portals: 4.0 − 0.01 = 3.99; −5% (0.1995) − 0.1 = 3.6905
    # Tonnel:  5.0 − 0.01 = 4.99; −4% (0.1996) − 0.001 = 4.7894
    nets = {o.market: o.net_nano for o in d.options}
    assert nets == {"portals": 3_690_500_000, "tonnel": 4_789_400_000}
    assert d.best.market == "tonnel"
    assert d.profit_nano == 1_789_400_000
    assert d.roi_bps == 5964  # 1.7894 / 3 = 59.64%
    assert d.discount_bps == 2500  # (4.0 − 3) / 4.0
    assert d.estimate is True  # комиссии не проверены
    assert d.too_good is False
    assert d.cheapest_elsewhere == {"portals": 4 * TON, "tonnel": 5_500_000_000}  # tonnel +10%
    assert d.cheaper_elsewhere is None


def test_deal_sales_cap_resale():
    target = books()["portals"][0]
    sales = [
        sale(
            str(i),
            p,
            market="tonnel",
            model="Watcher",
            backdrop="Black",
            occurred_at=NOW - timedelta(hours=i + 1),
        )
        for i, p in enumerate(["4.5", "4.6", "4.7"])
    ] + [
        sale(
            "old",
            "1",
            market="tonnel",
            model="Watcher",
            backdrop="Black",
            occurred_at=NOW - timedelta(hours=30),
        )
    ]
    d = evaluate(target, books(), sales, NOW)
    tonnel = next(o for o in d.options if o.market == "tonnel")
    # медиана 4.6 < 4.99 → перепродажа 4.6; −4% (0.184) − 0.001 = 4.415
    assert (tonnel.resale_nano, tonnel.capped_by_sales, tonnel.sales_count) == (
        4_600_000_000,
        True,
        3,
    )
    assert tonnel.net_nano == 4_415_000_000
    assert d.profit_nano == 1_415_000_000


def test_deal_tonnel_buy_fee_and_cheaper_elsewhere():
    b = books()
    target = listing("x2", "4.5", market="tonnel", model="Watcher", backdrop="Black")
    b["tonnel"].append(target)
    d = evaluate(target, b, [], NOW)
    assert d.all_in_nano == 4_950_000_000  # 4.5 × 1.1
    assert d.cheaper_elsewhere == "portals"  # 3 TON на Portals дешевле 4.95
    assert d.discount_bps == 1000  # (5.0 − 4.5) / 5.0


def test_deal_verified_fees_drop_estimate_flag():
    v = {
        m: FeeSchedule(f.buy_bps, f.sell_bps, f.withdraw_nano, True, "тест")
        for m, f in DEFAULT_FEES.items()
    }
    d = evaluate(books()["portals"][0], books(), [], NOW, fees=v)
    assert d.estimate is False


def test_deal_without_comparables():
    t = listing("lonely", 3, collection="Rare One")
    d = evaluate(t, {"portals": [t]}, [], NOW)
    assert d.best is None and d.profit_nano is None and d.estimate is True


def test_deal_too_good_and_locked():
    b = books()
    t = listing(
        "cheap", "0.9", model="Watcher", backdrop="Black", locked_until=NOW + timedelta(days=1)
    )
    b["portals"].append(t)
    d = evaluate(t, b, [], NOW)
    assert d.too_good is True  # 0.9 < 25% от 4.0
    assert d.locked is True
