"""Табличные тесты флора (AGENTS.md §8, PLAN 3.1). Цены в TON для читаемости."""

from dataclasses import replace

import pytest

from app.pricing.floor import (
    FloorConfig,
    cluster_floor,
    estimate_floor,
    jump_adjusted,
    looks_too_good,
)
from tests.factories import listing

TON = 1_000_000_000


def n(*tons):
    return [round(t * 100) * TON // 100 for t in tons]


@pytest.mark.parametrize(
    ("prices", "expected"),
    [
        # кластер: 3.57 и ещё ≥2 в пределах +10% (≤3.927)
        (n(3.57, 3.57, 3.58, 3.59, 3.60, 3.62), (n(3.57)[0], 6)),
        # приманка 1.0 одна → кластер начинается с 3.57
        (n(1.0, 3.57, 3.58, 3.90), (n(3.57)[0], 3)),
        # три приманки рядом (1.0, 1.05, 1.09) образуют кластер — известное ограничение
        (n(1.0, 1.05, 1.09, 3.57), (n(1.0)[0], 3)),
        # граница: 4.0·1.1 = 4.4 входит
        (n(4.0, 4.4, 4.4), (n(4.0)[0], 3)),
        # 4.41 уже не входит
        (n(4.0, 4.2, 4.41), None),
        # разброс 3.57 → 5.00 — кластера нет
        (n(3.57, 3.90, 4.10, 5.00), None),
        ([], None),
    ],
)
def test_cluster_floor(prices, expected):
    assert cluster_floor(sorted(prices), k=3, band_bps=1000) == expected


def book(*specs):
    """(id, цена, модель, фон)"""
    return [listing(i, p, model=m, backdrop=b) for i, p, m, b in specs]


TARGET = listing("t", 3, model="Watcher", backdrop="Black")


@pytest.mark.parametrize(
    ("items", "floor_ton", "basis", "confidence", "method"),
    [
        # модель+фон: 3 сопоставимых, кластер 4.0/4.1/4.3 → med
        (
            [
                ("a", "4.0", "Watcher", "Black"),
                ("b", "4.1", "Watcher", "Black"),
                ("c", "4.3", "Watcher", "Black"),
                ("d", "2", "Other", "Black"),
            ],
            "4.0",
            "model_backdrop",
            "med",
            "cluster",
        ),
        # модель+фон мало (2) → уровень «модель»: 5 шт., кластер с 5.0
        (
            [
                ("a", "5.0", "Watcher", "Black"),
                ("b", "5.2", "Watcher", "Black"),
                ("c", "5.1", "Watcher", "Red"),
                ("d", "6", "Watcher", "Blue"),
                ("e", "9", "Watcher", "Green"),
            ],
            "5.0",
            "model",
            "med",
            "cluster",
        ),
        # модель: 3 шт. без кластера → медиана трёх дешёвых, low
        (
            [
                ("a", "5", "Watcher", "Red"),
                ("b", "7", "Watcher", "Blue"),
                ("c", "9", "Watcher", "Green"),
            ],
            "7",
            "model",
            "low",
            "thin_median",
        ),
        # high: 8+ сопоставимых и кластер
        (
            [(str(i), str(4 + i / 100), "Watcher", "Black") for i in range(8)],
            "4",
            "model_backdrop",
            "high",
            "cluster",
        ),
    ],
)
def test_estimate_floor(items, floor_ton, basis, confidence, method):
    est = estimate_floor(TARGET, book(*items), FloorConfig())
    assert est is not None
    assert est.floor_nano == int(float(floor_ton) * 100) * TON // 100
    assert (est.basis, est.confidence, est.method) == (basis, confidence, method)


def test_collection_level_needs_five():
    items = [listing(str(i), 5 + i, model=f"M{i}", backdrop=f"B{i}") for i in range(4)]
    assert estimate_floor(TARGET, items, FloorConfig()) is None
    items.append(listing("x", 5, model="M9", backdrop="B9"))
    est = estimate_floor(TARGET, items, FloorConfig())
    assert est is not None and est.basis == "collection"
    assert est.floor_nano == 5 * TON and est.comparables == 5


def test_excludes_self_traps_and_other_collections():
    same = [
        listing("t", 3, model="Watcher", backdrop="Black"),  # сам лот
        listing("bundle", 1, model="Watcher", backdrop="Black", is_bundle=True),
        listing("pm", 1, model="Watcher", backdrop="Black", is_premarket=True),
        listing("auc", 1, model="Watcher", backdrop="Black", is_auction=True),
        listing("other", 1, collection="Plush Pepe", model="Watcher", backdrop="Black"),
        listing("a", 4, model="Watcher", backdrop="Black"),
        listing("b", 4, model="Watcher", backdrop="Black"),
        listing("c", 4, model="Watcher", backdrop="Black"),
    ]
    est = estimate_floor(TARGET, same, FloorConfig())
    assert est is not None and est.floor_nano == 4 * TON and est.comparables == 3


@pytest.mark.parametrize(
    ("prev", "now", "before", "after"),
    [
        (10 * TON, 12 * TON, "high", "high"),  # +20% — норма
        (10 * TON, 13 * TON, "high", "med"),  # +30% за час — понизить
        (10 * TON, 7 * TON, "med", "low"),  # −30%
        (10 * TON, 7 * TON, "low", "low"),
        (None, 7 * TON, "high", "high"),
    ],
)
def test_jump_adjusted(prev, now, before, after):
    est = estimate_floor(
        TARGET,
        [listing(str(i), "4", model="Watcher", backdrop="Black") for i in range(8)],
        FloorConfig(),
    )
    est = replace(est, floor_nano=now, confidence=before)
    assert jump_adjusted(est, prev, FloorConfig()).confidence == after


@pytest.mark.parametrize(
    ("price", "floor", "suspicious"),
    [(TON, 4 * TON, False), (TON - 1, 4 * TON, True), (0, 4 * TON, True)],
)
def test_too_good(price, floor, suspicious):
    assert looks_too_good(price, floor, FloorConfig()) is suspicious
