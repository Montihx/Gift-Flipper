"""Итоговая оценка листинга — `Deal` (PLAN 3.3, 3.5, 3.6).

Для листинга на маркете A:
- all-in = цена + комиссия покупки A;
- для каждого маркета B с флором по сопоставимым: перепродажа = min(флор_B − undercut,
  медиана продаж B за 24 ч при ≥3 продажах), net_B = перепродажа − комиссия продажи B − вывод;
- выбирается B с максимальным net; прибыль = net − all-in;
- `estimate=True`, пока комиссии пары (A, B) не проверены (D-009).
Флор по Telegram — только сигнал (`tg_above_value`), на выбор не влияет.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime

from app.markets.base import Listing, Market, Sale
from app.pricing.aliases import same_collection
from app.pricing.fees import DEFAULT_FEES, FeeSchedule, all_in_price, net_after_sale, verified_pair
from app.pricing.floor import FloorConfig, FloorEstimate, estimate_floor, looks_too_good
from app.pricing.sales import check_with_sales, matching_sales

UNDERCUT_NANO = 10_000_000  # 0.01 TON — перепродажа чуть ниже флора (topcvetok config.json:76)


@dataclass(frozen=True, slots=True)
class ResaleOption:
    market: Market
    floor: FloorEstimate
    resale_nano: int
    net_nano: int
    sales_count: int
    capped_by_sales: bool


@dataclass(frozen=True, slots=True)
class Deal:
    listing: Listing
    all_in_nano: int
    best: ResaleOption | None
    options: tuple[ResaleOption, ...]
    profit_nano: int | None
    roi_bps: int | None  # прибыль / all-in, базисные пункты
    discount_bps: int | None  # насколько цена ниже флора своего маркета
    estimate: bool  # комиссии не проверены → «оценка»
    too_good: bool
    locked: bool
    cheapest_elsewhere: dict[Market, int] = field(default_factory=dict)
    tg_above_value: bool | None = None

    @property
    def cheaper_elsewhere(self) -> Market | None:
        """Маркет, где та же модель дешевле по all-in (правило «спросить», SUMMARY §2)."""
        best = None
        for market, price in self.cheapest_elsewhere.items():
            if (
                market != self.listing.market
                and price < self.all_in_nano
                and (best is None or price < self.cheapest_elsewhere[best])
            ):
                best = market
        return best


def _cheapest_by_market(
    target: Listing, books: Mapping[Market, Iterable[Listing]], fees: Mapping[Market, FeeSchedule]
) -> dict[Market, int]:
    out: dict[Market, int] = {}
    for market, book in books.items():
        prices = [
            all_in_price(market, x.price_nano, dict(fees))
            for x in book
            if same_collection(x.collection, target.collection)
            and x.model == target.model
            and x.listing_id != target.listing_id
            and not (x.is_bundle or x.is_premarket or x.is_auction)
        ]
        if prices:
            out[market] = min(prices)
    return out


def evaluate(
    target: Listing,
    books: Mapping[Market, Iterable[Listing]],
    sales: Iterable[Sale],
    now: datetime,
    *,
    fees: Mapping[Market, FeeSchedule] = DEFAULT_FEES,
    floor_cfg: FloorConfig | None = None,
    undercut_nano: int = UNDERCUT_NANO,
    min_sales: int = 3,
    tg_above_value: bool | None = None,
) -> Deal:
    floor_cfg = floor_cfg or FloorConfig()
    fee_map = dict(fees)
    books = {m: list(b) for m, b in books.items()}
    sales = list(sales)
    all_in = all_in_price(target.market, target.price_nano, fee_map)

    options: list[ResaleOption] = []
    own_floor: FloorEstimate | None = None
    for market, book in books.items():
        # Книга маркета B приводится к коллекции цели (алиасы) и рынку B.
        same = [x for x in book if same_collection(x.collection, target.collection)]
        probe = Listing(
            market=market,
            listing_id=target.listing_id if market == target.market else "",
            collection=target.collection,
            model=target.model,
            backdrop=target.backdrop,
            symbol=target.symbol,
            number=target.number,
            price_nano=target.price_nano,
        )
        normalized = [
            x if x.collection == target.collection else _with_collection(x, target.collection)
            for x in same
        ]
        est = estimate_floor(probe, normalized, floor_cfg)
        if est is None:
            continue
        if market == target.market:
            own_floor = est
        market_sales = [s for s in sales if s.market == market]
        prices = matching_sales(probe, market_sales, est.basis, now)
        check = check_with_sales(est.floor_nano - undercut_nano, prices, min_sales)
        net = net_after_sale(market, max(check.resale_nano, 0), fee_map)
        options.append(
            ResaleOption(market, est, check.resale_nano, net, check.count, check.capped_by_sales)
        )

    best = max(options, key=lambda o: o.net_nano, default=None)
    profit = best.net_nano - all_in if best else None
    roi = profit * 10_000 // all_in if (profit is not None and all_in > 0) else None
    discount = None
    if own_floor is not None and own_floor.floor_nano > 0:
        discount = (own_floor.floor_nano - target.price_nano) * 10_000 // own_floor.floor_nano
    estimate = best is None or not verified_pair(target.market, best.market, fee_map)
    return Deal(
        listing=target,
        all_in_nano=all_in,
        best=best,
        options=tuple(sorted(options, key=lambda o: -o.net_nano)),
        profit_nano=profit,
        roi_bps=roi,
        discount_bps=discount,
        estimate=estimate,
        too_good=bool(
            own_floor and looks_too_good(target.price_nano, own_floor.floor_nano, floor_cfg)
        ),
        locked=target.locked_until is not None and target.locked_until > now,
        cheapest_elsewhere=_cheapest_by_market(target, books, fee_map),
        tg_above_value=tg_above_value,
    )


def _with_collection(item: Listing, collection: str) -> Listing:
    return replace(item, collection=collection)
