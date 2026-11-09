from decimal import Decimal

import pytest

from app.money import apply_bps, format_ton, nano_to_ton, ton_to_nano


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("44", 44_000_000_000),  # Portals: цена строкой (README portalsmp)
        ("31.43", 31_430_000_000),
        ("1.85", 1_850_000_000),  # пример из кода aportalsmp
        (" 0.5 ", 500_000_000),
        ("0.000000001", 1),
        (Decimal("3.57"), 3_570_000_000),  # Tonnel: число JSON, распарсенное как Decimal
        (12, 12_000_000_000),
        ("0", 0),
        ("1e2", 100_000_000_000),
    ],
)
def test_ton_to_nano(value, expected):
    assert ton_to_nano(value) == expected


@pytest.mark.parametrize("value", ["abc", "", "NaN", "Infinity", "0.0000000001"])
def test_ton_to_nano_rejects(value):
    with pytest.raises(ValueError):
        ton_to_nano(value)


@pytest.mark.parametrize("value", [1.85, True])
def test_ton_to_nano_rejects_float_and_bool(value):
    with pytest.raises(TypeError):
        ton_to_nano(value)


@pytest.mark.parametrize(
    ("nano", "ton", "shown"),
    [
        (44_000_000_000, Decimal("44"), "44.00"),
        (1_850_000_000, Decimal("1.85"), "1.85"),
        (1_859_999_999, Decimal("1.859999999"), "1.85"),  # показ усекает вниз
        (1, Decimal("0.000000001"), "0.00"),
    ],
)
def test_nano_to_ton_and_format(nano, ton, shown):
    assert nano_to_ton(nano) == ton
    assert format_ton(nano) == shown


@pytest.mark.parametrize(
    ("nano", "bps", "expected"),
    [
        (10_000_000_000, 1000, 1_000_000_000),  # 10% от 10 TON
        (10_000_000_000, 500, 500_000_000),  # 5%
        (3_570_000_000, 200, 71_400_000),  # 2% от 3.57 TON
        (1, 500, 0),  # округление вниз
    ],
)
def test_apply_bps(nano, bps, expected):
    assert apply_bps(nano, bps) == expected


def test_nano_to_ton_rejects_non_int():
    with pytest.raises(TypeError):
        nano_to_ton(1.0)  # type: ignore[arg-type]
