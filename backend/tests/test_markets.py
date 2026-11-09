from datetime import UTC, datetime

import pytest

from app.markets import mrkt, portals, tonnel
from app.markets.base import MarketClient, SchemaError, SearchQuery, rarity_permille, strip_rarity
from app.markets.http import HttpError
from app.markets.mock import MockClient
from tests.conftest import FakeTransport, load_fixture, ok, ok_fixture

P1 = "0b6f2c1e-1111-4a2b-9c3d-000000000001"


# --- Portals ---------------------------------------------------------------


def portals_client(make_http, t, auth=None):
    http = make_http("portals", portals.BASE_URL, portals.READ_ROUTES, t, portals.HEADERS)
    return portals.PortalsClient(http, auth=auth)


async def test_portals_search_public_and_parsed(make_http):
    t = (
        FakeTransport()
        .add("GET", "/api/collections", ok_fixture("code/portals/collections.json"))
        .add("GET", "/api/nfts/search", ok_fixture("code/portals/search.json"))
    )
    c = portals_client(make_http, t)
    items = await c.search(SearchQuery(collection="Evil Eye", model="Watcher", sort="price_asc"))
    first = items[0]
    assert first.listing_id == P1
    assert first.price_nano == 8_000_000_000
    assert (first.model, first.backdrop, first.symbol, first.number) == (
        "Watcher",
        "Onyx Black",
        "Moon",
        42,
    )
    assert first.locked_until is None  # unlocks_at в прошлом
    assert (first.model_rarity_pm, first.backdrop_rarity_pm, first.symbol_rarity_pm) == (15, 20, 4)
    assert items[1].price_nano == 9_150_000_000
    assert items[2].locked_until == datetime(2999, 1, 1, tzinfo=UTC)
    search = t.sent[-1]
    assert "Authorization" not in search.headers  # публичный маршрут без токена
    assert search.params["collection_ids"] == "7d1e0c55-2222-4b3c-8d4e-0000000000aa"
    assert search.params["sort_by"] == "price asc"
    assert search.params["filter_by_models"] == "Watcher"


async def test_portals_search_drops_non_listed(make_http):
    t = FakeTransport().add(
        "GET", "/api/nfts/search", ok_fixture("code/portals/search_sold_item.json")
    )
    assert await portals_client(make_http, t).search(SearchQuery()) == []


async def test_portals_floors_from_collections(make_http):
    t = FakeTransport().add("GET", "/api/collections", ok_fixture("code/portals/collections.json"))
    floors = await portals_client(make_http, t).floors()
    assert [(f.collection, f.floor_nano) for f in floors] == [
        ("Evil Eye", 7_900_000_000),
        ("Plush Pepe", 5_200_000_000_000),
    ]


async def test_portals_sales_need_auth_and_parse(make_http):
    async def auth():
        return "query_id=X&hash=Y"

    t = FakeTransport().add("GET", "/api/market/actions/", ok_fixture("code/portals/actions.json"))
    sales = await portals_client(make_http, t, auth).recent_sales()
    assert len(sales) == 1  # listing отброшен
    s = sales[0]
    assert s.price_nano == 9_150_000_000
    assert s.occurred_at == datetime(2026, 11, 9, 9, 40, tzinfo=UTC)
    assert t.sent[0].headers["Authorization"] == "tma query_id=X&hash=Y"
    assert t.sent[0].params["action_types"] == "buy"


async def test_portals_get_listing_404(make_http):
    t = FakeTransport().add("GET", f"/api/nfts/{P1}", ok({}, status=404))
    assert await portals_client(make_http, t).get_listing(P1) is None


async def test_portals_get_listing(make_http):
    t = FakeTransport().add("GET", f"/api/nfts/{P1}", ok_fixture("code/portals/nft.json"))
    listing = await portals_client(make_http, t).get_listing(P1)
    assert listing is not None and listing.price_nano == 8_000_000_000


@pytest.mark.parametrize("price", [8.5, None, {"x": 1}])
def test_portals_rejects_bad_price(price):
    gift = load_fixture("code/portals/nft.json") | {"price": price}
    with pytest.raises((SchemaError, TypeError)):
        portals.parse_gift(gift)


# --- MRKT ------------------------------------------------------------------


def mrkt_client(make_http, t):
    async def init_data():
        return "query_id=M&hash=H"

    http = make_http("mrkt", mrkt.BASE_URL, mrkt.READ_ROUTES, t, mrkt.HEADERS)
    return mrkt.MrktClient(http, init_data)


async def test_mrkt_login_and_search(make_http):
    t = (
        FakeTransport()
        .add("POST", "/api/v1/auth", ok_fixture("code/mrkt/auth.json"))
        .add("POST", "/api/v1/gifts/saling", ok_fixture("code/mrkt/saling.json"))
    )
    items = await mrkt_client(make_http, t).search(
        SearchQuery(collection="Evil Eye", sort="price_asc", limit=50)
    )
    assert [x.price_nano for x in items] == [10_000_000_000, 8_500_000_000]  # isMine отброшен
    assert items[1].is_premarket
    auth, search = t.sent
    assert auth.json_body == {"data": "query_id=M&hash=H"}
    assert search.headers["Authorization"] == "test-token-not-real"
    assert search.headers["Cookie"] == "access_token=test-token-not-real"
    assert search.headers["Referer"] == "https://cdn.tgmrkt.io/"
    body = search.json_body
    assert body["count"] == 20  # потолок MAX_COUNT
    assert body["collectionNames"] == ["Evil Eye"]
    assert (body["ordering"], body["lowToHigh"], body["cursor"]) == ("Price", True, "")


async def test_mrkt_relogin_on_401(make_http):
    t = (
        FakeTransport()
        .add("POST", "/api/v1/auth", ok({"token": "t1"}), ok({"token": "t2"}))
        .add("POST", "/api/v1/gifts/saling", ok({}, status=401), ok({"gifts": [], "cursor": None}))
    )
    assert await mrkt_client(make_http, t).search(SearchQuery()) == []
    auths = [s for s in t.sent if s.path == "/api/v1/auth"]
    assert len(auths) == 2
    assert t.sent[-1].headers["Authorization"] == "t2"


async def test_mrkt_401_twice_raises(make_http):
    t = (
        FakeTransport()
        .add("POST", "/api/v1/auth", ok({"token": "t"}))
        .add("POST", "/api/v1/gifts/saling", ok({}, status=401))
    )
    with pytest.raises(HttpError):
        await mrkt_client(make_http, t).search(SearchQuery())


async def test_mrkt_floors_and_sales(make_http):
    t = (
        FakeTransport()
        .add("POST", "/api/v1/auth", ok({"token": "t"}))
        .add("GET", "/api/v1/gifts/collections", ok_fixture("code/mrkt/collections.json"))
        .add("POST", "/api/v1/feed", ok_fixture("code/mrkt/feed.json"))
    )
    c = mrkt_client(make_http, t)
    floors = await c.floors()
    assert [(f.collection, f.floor_nano) for f in floors] == [("Evil Eye", 7_900_000_000)]
    sales = await c.recent_sales()
    assert len(sales) == 1
    assert (sales[0].event_id, sales[0].price_nano) == ("f-1", 9_500_000_000)
    assert t.sent[-1].json_body["type"] == ["Sale"]


@pytest.mark.parametrize("price", ["10", 1.5, 0, True])
def test_mrkt_rejects_non_nano(price):
    gift = load_fixture("code/mrkt/saling.json")["gifts"][0] | {"salePrice": price}
    with pytest.raises(SchemaError):
        mrkt.parse_gift(gift)


# --- Tonnel ----------------------------------------------------------------


def tonnel_client(make_http, t, init_data=None):
    http = make_http("tonnel", tonnel.BASE_URL, tonnel.READ_ROUTES, t, tonnel.HEADERS)
    return tonnel.TonnelClient(http, init_data)


async def test_tonnel_search_body_and_filtering(make_http):
    t = FakeTransport().add("POST", "/api/pageGifts", ok_fixture("code/tonnel/pageGifts.json"))
    items = await tonnel_client(make_http, t).search(
        SearchQuery(collection="Chill Flame", model="Lego", sort="price_asc", limit=100)
    )
    # бандл (gift_id<0), аукцион и USDT отброшены
    assert [(x.listing_id, x.price_nano) for x in items] == [
        ("42", 5_500_000_000),
        ("43", 3_570_000_000),
    ]
    assert (items[0].model, items[0].backdrop, items[0].symbol) == ("Lego", "Black", "Star")
    assert (items[0].model_rarity_pm, items[0].backdrop_rarity_pm) == (30, 10)
    body = t.sent[0].json_body
    assert body["limit"] == 30
    assert body["user_auth"] == ""
    assert isinstance(body["filter"], str) and isinstance(body["sort"], str)
    assert '"gift_name":"Chill Flame"' in body["filter"]
    assert '"model":{"$regex":"^Lego \\\\("}' in body["filter"]
    assert body["sort"] == '{"price":1,"gift_id":-1}'


def test_tonnel_events():
    events = load_fixture("code/tonnel/events.json")["events"]
    parsed = [tonnel.parse_event(e) for e in events]
    created, changed, dutch, premarket, sale = parsed
    assert isinstance(created, tonnel.ListingEvent) and created.kind == "created"
    assert created.listing.price_nano == 5_500_000_000
    assert created.listing.collection == "Chill Flame"
    assert isinstance(changed, tonnel.ListingEvent) and changed.listing.price_nano == 5_000_000_000
    assert dutch is None and premarket is None
    assert sale.event_id == "sale-77"
    assert sale.price_nano == 3_600_000_000
    assert (sale.model, sale.backdrop) == ("Rare Model", "Black")
    assert sale.occurred_at == datetime(2026, 11, 9, 10, 5, tzinfo=UTC)


async def test_tonnel_floors_need_auth(make_http):
    assert await tonnel_client(make_http, FakeTransport()).floors() == []

    async def init_data():
        return "query_id=T"

    t = FakeTransport().add("POST", "/api/filterStats", ok_fixture("code/tonnel/filterStats.json"))
    floors = await tonnel_client(make_http, t, init_data).floors()
    assert [(f.collection, f.model, f.floor_nano, f.count) for f in floors] == [
        ("Chill Flame", "Lego", 3_570_000_000, 12),
    ]
    assert t.sent[0].json_body == {"authData": "query_id=T"}


async def test_tonnel_replay_events(make_http):
    t = FakeTransport().add("GET", "/api/marketplace/events", ok_fixture("code/tonnel/events.json"))
    events, nxt = await tonnel_client(make_http, t).replay_events("event-0")
    assert len(events) == 5 and nxt == "sale-77"
    assert t.sent[0].url.startswith("https://gifts.coffin.meme/")
    assert t.sent[0].params == {"after": "event-0", "limit": 100}


async def test_tonnel_sales_from_stream_buffer(make_http):
    c = tonnel_client(make_http, FakeTransport())
    sale = tonnel.parse_event(load_fixture("code/tonnel/events.json")["events"][4])
    c.remember_sale(sale)
    assert await c.recent_sales() == [sale]


async def test_tonnel_stream_events():
    class FakeWS:
        def __init__(self):
            self.frames = [(b'{"eventId":"e","price":5.5}', 1), (b"not json", 1)]
            self.closed = False

        async def recv(self):
            if not self.frames:
                raise ConnectionError("closed")
            return self.frames.pop(0)

        async def close(self):
            self.closed = True

    ws = FakeWS()

    async def connect():
        return ws

    got = []
    with pytest.raises(ConnectionError):
        async for ev in tonnel.stream_events(connect):
            got.append(ev)
    assert len(got) == 1 and str(got[0]["price"]) == "5.5"
    assert ws.closed


# --- общее -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "clean"),
    [("Black (1%)", "Black"), ("Lego (0.5%)", "Lego"), ("Onyx Black", "Onyx Black"), (None, None)],
)
def test_strip_rarity(raw, clean):
    assert strip_rarity(raw) == clean


@pytest.mark.parametrize(
    ("raw", "pm"),
    [("Black (1%)", 10), ("Lego (0.5%)", 5), ("X (2,5%)", 25), ("Onyx", None), (None, None)],
)
def test_rarity_permille(raw, pm):
    assert rarity_permille(raw) == pm


async def test_mock_client_protocol_and_filters():
    from tests.factories import listing

    m = MockClient("portals", listings=[listing(price=9), listing(listing_id="b", price=8)])
    assert isinstance(m, MarketClient)
    res = await m.search(SearchQuery(sort="price_asc"))
    assert [x.listing_id for x in res] == ["b", "a"]
    m.fail_with = RuntimeError("down")
    with pytest.raises(RuntimeError):
        await m.floors()
