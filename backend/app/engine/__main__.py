"""Цикл наблюдения: `python -m app.engine --dry-run [--plan | --live] [--once]`.

- без флагов режима — mock-клиенты на фикстурах (`tests/fixtures/code`), сеть не трогается;
- `--plan` — печатает список запросов живого режима и выходит (показать владельцу);
- `--live` — живые запросы ТОЛЬКО на чтение; требует `LIVE_READS_APPROVED=yes` в окружении
  (владелец ставит после просмотра `--plan`) и Telethon-сессию в `data/` с правами 600.
  `--record DIR` сохраняет ответы для фикстур (секреты маскируются, файлы 600).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from app.engine.plan import format_plan, live_plan
from app.markets.base import Listing, MarketClient, MarketError, SearchQuery
from app.money import format_ton
from app.security import setup_logging
from app.settings import get_settings


def format_listing(x: Listing) -> str:
    num = f"#{x.number}" if x.number is not None else ""
    attrs = " / ".join(a or "—" for a in (x.model, x.backdrop, x.symbol))
    price = format_ton(x.price_nano)
    return f"{x.market:<8} {x.collection} {num:<8} {attrs:<40} {price:>10} TON  {x.url or ''}"


def mock_clients() -> list[MarketClient]:
    from app.engine.fixtures import fixture_clients

    return fixture_clients()


async def poll_once(clients: Sequence[MarketClient], query: SearchQuery) -> list[Listing]:
    out: list[Listing] = []
    for c in clients:
        try:
            out.extend(await c.search(query))
        except MarketError as exc:
            print(f"{c.market}: ошибка: {exc}", file=sys.stderr)
    return out


async def run(args: argparse.Namespace) -> int:
    settings = get_settings()
    if args.plan:
        print(format_plan(live_plan(args.collection), settings.listings_poll_interval_s))
        return 0
    if args.live:
        if os.environ.get("LIVE_READS_APPROVED") != "yes":
            print(
                "Живой режим не разрешён: сначала `--plan`, затем владелец ставит "
                "LIVE_READS_APPROVED=yes.",
                file=sys.stderr,
            )
            return 2
        from app.engine.live import live_clients

        clients, close = await live_clients(settings, record_dir=args.record)
        if args.notify:
            from app.engine.watch import run_watch

            try:
                return await run_watch(settings, clients, args.once)
            finally:
                for c in clients:
                    await c.aclose()
                await close()
    else:
        clients, close = mock_clients(), None
    try:
        query = SearchQuery(sort="latest", limit=args.limit)
        while True:
            for x in await poll_once(clients, query):
                print(format_listing(x))
            if args.once:
                return 0
            await asyncio.sleep(settings.listings_poll_interval_s)
    finally:
        for c in clients:
            await c.aclose()
        if close is not None:
            await close()


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.engine")
    p.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="обязательный флаг: покупки выключены (D-003)",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="показать запросы живого режима")
    mode.add_argument("--live", action="store_true", help="живые запросы на чтение")
    p.add_argument("--once", action="store_true", help="один цикл и выход")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--collection", action="append", default=[], help="коллекция (можно несколько)")
    p.add_argument("--record", type=Path, default=None, help="папка для записи ответов (live)")
    p.add_argument("--notify", action="store_true", help="пуши по пресетам в бот (только с --live)")
    args = p.parse_args(argv)
    if args.notify and not args.live:
        p.error("--notify работает только с --live")
    setup_logging(get_settings().log_level)
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
