"""MockClient для тестов и `--mock` режима движка (PLAN 2.7). Сети не трогает."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.markets.base import CollectionFloor, Listing, Market, Sale, SearchQuery


@dataclass
class MockClient:
    market: Market
    listings: list[Listing] = field(default_factory=list)
    sales: list[Sale] = field(default_factory=list)
    floor_list: list[CollectionFloor] = field(default_factory=list)
    calls: list[tuple[str, object]] = field(default_factory=list)
    fail_with: Exception | None = None

    def _maybe_fail(self) -> None:
        if self.fail_with is not None:
            raise self.fail_with

    async def search(self, query: SearchQuery) -> list[Listing]:
        self.calls.append(("search", query))
        self._maybe_fail()
        items = [
            x
            for x in self.listings
            if (query.collection is None or x.collection == query.collection)
            and (query.model is None or x.model == query.model)
            and (query.backdrop is None or x.backdrop == query.backdrop)
            and (query.symbol is None or x.symbol == query.symbol)
        ]
        if query.sort == "price_asc":
            items.sort(key=lambda x: x.price_nano)
        return items[: query.limit]

    async def floors(self) -> list[CollectionFloor]:
        self.calls.append(("floors", None))
        self._maybe_fail()
        return list(self.floor_list)

    async def recent_sales(self, limit: int = 20) -> list[Sale]:
        self.calls.append(("recent_sales", limit))
        self._maybe_fail()
        return self.sales[:limit]

    async def get_listing(self, listing_id: str) -> Listing | None:
        self.calls.append(("get_listing", listing_id))
        self._maybe_fail()
        return next((x for x in self.listings if x.listing_id == listing_id), None)

    async def aclose(self) -> None:
        self.calls.append(("aclose", None))
