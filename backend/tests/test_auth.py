from datetime import UTC, datetime, timedelta

import pytest

from app.markets.auth import TelethonInitDataProvider, TokenCache, extract_init_data
from app.markets.base import AuthRequired

URL = (
    "https://portal-market.com/#tgWebAppData=query_id%3DAAH1%26user%3D%257B%2522id%2522%253A1%257D"
    "%26auth_date%3D1700000000%26hash%3Dabc&tgWebAppVersion=8.0&tgWebAppPlatform=desktop"
)


def test_extract_init_data():
    assert extract_init_data(URL) == (
        "query_id=AAH1&user=%7B%22id%22%3A1%7D&auth_date=1700000000&hash=abc"
    )


@pytest.mark.parametrize("bad", ["https://x/#foo=1", "https://x/#tgWebAppData=&tgWebAppVersion=1"])
def test_extract_init_data_rejects(bad):
    with pytest.raises(ValueError):
        extract_init_data(bad)


class FakeTelethon:
    def __init__(self):
        self.requests = []

    async def get_input_entity(self, name):
        return f"peer:{name}"

    async def __call__(self, req):
        self.requests.append(req)

        class R:
            url = URL

        return R()


async def test_telethon_provider_uses_spec():
    client = FakeTelethon()
    p = TelethonInitDataProvider(client)
    data = await p.init_data("portals")
    assert data.startswith("query_id=AAH1")
    req = client.requests[0]
    assert req.peer == "peer:portals"
    assert req.app.short_name == "market"
    assert req.platform == "desktop"
    await p.init_data("mrkt")
    assert client.requests[1].app.short_name == "app"


async def test_telethon_provider_tonnel_not_configured():
    with pytest.raises(AuthRequired):
        await TelethonInitDataProvider(FakeTelethon()).init_data("tonnel")


async def test_token_cache_refresh_and_invalidate():
    now = {"t": datetime(2026, 11, 9, tzinfo=UTC)}
    calls = []

    async def fetch(market):
        calls.append(market)
        return f"tok{len(calls)}"

    cache = TokenCache(fetch, max_age=timedelta(hours=1), now=lambda: now["t"])
    assert await cache.get("mrkt") == "tok1"
    assert await cache.get("mrkt") == "tok1"
    now["t"] += timedelta(hours=1)
    assert await cache.get("mrkt") == "tok2"
    cache.invalidate("mrkt")
    assert await cache.get("mrkt") == "tok3"
