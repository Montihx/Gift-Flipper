import re

import pytest

from app.engine.__main__ import format_listing, main, poll_once
from app.engine.fixtures import fixture_clients
from app.engine.plan import format_plan, live_plan
from app.markets import mrkt, portals, tonnel
from app.markets.base import MarketError, SearchQuery
from app.markets.mock import MockClient
from tests.factories import listing

WRITE_WORDS = re.compile(
    r"buy|sale(?!s)|bulk-list|withdraw|offers|listForSale|cancel|return|/list\b"
)


async def test_fixture_clients_cover_three_markets():
    clients = fixture_clients()
    got = await poll_once(clients, SearchQuery(limit=50))
    assert {x.market for x in got} == {"portals", "mrkt", "tonnel"}
    # фильтры активных лотов те же, что у боевых клиентов
    assert all(not x.is_bundle and not x.is_auction for x in got)
    assert {x.listing_id for x in got if x.market == "tonnel"} == {"42", "43"}


async def test_poll_once_survives_market_error(capsys):
    bad = MockClient("mrkt", fail_with=MarketError("down"))
    good = MockClient("portals", listings=[listing()])
    got = await poll_once([bad, good], SearchQuery())
    assert len(got) == 1
    assert "mrkt: ошибка: down" in capsys.readouterr().err


def test_format_listing():
    line = format_listing(listing(price="8.5", url="https://t.me/x"))
    assert "portals" in line and "Evil Eye #42" in line and "8.50 TON" in line


def test_plan_has_no_write_routes():
    for r in live_plan(["Plush Pepe"]):
        assert not WRITE_WORDS.search(r.url), r.url
    text = format_plan(live_plan([]), 5.0)
    assert "без фильтра" in text and "раз в 5 с" in text


@pytest.mark.parametrize("routes", [portals.READ_ROUTES, mrkt.READ_ROUTES, tonnel.READ_ROUTES])
def test_read_routes_have_no_write_paths(routes):
    for r in routes:
        assert not WRITE_WORDS.search(r.pattern), r.pattern


def test_live_requires_owner_approval(monkeypatch, capsys):
    monkeypatch.delenv("LIVE_READS_APPROVED", raising=False)
    assert main(["--dry-run", "--live", "--once"]) == 2
    assert "LIVE_READS_APPROVED" in capsys.readouterr().err


def test_dry_run_flag_required():
    with pytest.raises(SystemExit):
        main(["--once"])


def test_mock_run_prints(capsys):
    assert main(["--dry-run", "--once"]) == 0
    out = capsys.readouterr().out
    assert out.count("\n") == 7


def test_notify_requires_live():
    with pytest.raises(SystemExit):
        main(["--dry-run", "--notify", "--once"])
