"""Табличные тесты комиссий с конкретными числами (AGENTS.md §5, D-009)."""

import pytest

from app.pricing.fees import DEFAULT_FEES, FeeSchedule, all_in_price, net_after_sale

TON = 1_000_000_000


@pytest.mark.parametrize(
    ("market", "price", "all_in"),
    [
        ("portals", 10 * TON, 10 * TON),  # покупка 0%
        ("tonnel", 10 * TON, 11 * TON),  # +10% к цене листинга
        ("tonnel", 3_570_000_000, 3_927_000_000),
        ("mrkt", 10 * TON, 10 * TON),  # salePrice уже с надбавкой покупателя (фикстура topcvetok)
    ],
)
def test_all_in(market, price, all_in):
    assert all_in_price(market, price) == all_in


@pytest.mark.parametrize(
    ("market", "resale", "net"),
    [
        # 10 TON − 5% продажи − 0.1 TON вывода = 9.4 TON
        ("portals", 10 * TON, 9_400_000_000),
        # 10 TON − 4% − 0.001 TON = 9.599 TON
        ("tonnel", 10 * TON, 9_599_000_000),
        # 10 TON − 8% = 9.2 TON (вывод не известен → 0, помечено)
        ("mrkt", 10 * TON, 9_200_000_000),
        ("portals", 0, 0),  # не уходим в минус на выводе
    ],
)
def test_net_after_sale(market, resale, net):
    assert net_after_sale(market, resale) == net


def test_all_unverified_by_default():
    assert all(not f.verified for f in DEFAULT_FEES.values())
    assert all(f.source for f in DEFAULT_FEES.values())


def test_custom_schedule():
    s = FeeSchedule(buy_bps=250, sell_bps=300, withdraw_nano=0, verified=True, source="владелец")
    assert all_in_price("portals", 4 * TON, {"portals": s}) == 4_100_000_000
    assert net_after_sale("portals", 4 * TON, {"portals": s}) == 3_880_000_000


@pytest.mark.parametrize("bps", [-1, 10_001])
def test_schedule_validates(bps):
    with pytest.raises(ValueError):
        FeeSchedule(buy_bps=bps, sell_bps=0, withdraw_nano=0, verified=False, source="x")
