"""Mock-клиенты из фикстур `tests/fixtures/code` — разбор теми же парсерами, что и в бою."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.markets import mrkt, portals, tonnel
from app.markets.base import MarketClient
from app.markets.mock import MockClient
from app.settings import BACKEND_DIR

FIXTURES = BACKEND_DIR / "tests" / "fixtures" / "code"


def _load(name: str, root: Path = FIXTURES) -> Any:
    return json.loads((root / name).read_text("utf-8"), parse_float=Decimal)


def fixture_clients(root: Path = FIXTURES) -> list[MarketClient]:
    """Те же фильтры активных лотов, что у боевых клиентов."""
    p = [
        portals.parse_gift(g)
        for g in _load("portals/search.json", root)["results"]
        if g.get("status") == "listed"
    ]
    m = [
        mrkt.parse_gift(g)
        for g in _load("mrkt/saling.json", root)["gifts"]
        if g.get("isOnSale", True) and not g.get("isMine")
    ]
    t = [
        x
        for x in (
            tonnel.parse_gift(g)
            for g in _load("tonnel/pageGifts.json", root)
            if tonnel.is_active(g)
        )
        if not x.is_bundle
    ]
    return [
        MockClient("portals", listings=p),
        MockClient("mrkt", listings=m),
        MockClient("tonnel", listings=t),
    ]
