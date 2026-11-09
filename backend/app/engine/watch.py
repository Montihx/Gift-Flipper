"""Режим watch с пушами: `python -m app.engine --dry-run --live --notify`.

Только чтение маркетов + уведомления владельцу. Покупок нет (D-003).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from app.bot.notifier import AiogramApi, Notifier
from app.db import make_engine, make_sessionmaker
from app.engine.pipeline import Pipeline
from app.engine.store import save_sales
from app.markets.base import MarketClient
from app.rules.repo import active_rules
from app.settings import Settings
from app.timeutil import utcnow

log = logging.getLogger(__name__)


async def run_watch(settings: Settings, clients: Sequence[MarketClient], once: bool) -> int:
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties

    if settings.bot_token is None or settings.owner_chat_id is None:
        raise SystemExit("для --notify нужны BOT_TOKEN и OWNER_CHAT_ID в .env")
    bot = Bot(
        settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode="HTML")
    )
    sessions = make_sessionmaker(make_engine())
    notifier = Notifier(AiogramApi(bot), sessions, settings.webapp_url)
    pipeline = Pipeline(clients, notifier, settings.owner_chat_id)
    try:
        while True:
            async with sessions() as s:
                rules = await active_rules(s, settings.owner_chat_id)
            res = await pipeline.run_cycle(rules, utcnow())
            async with sessions() as s:
                await save_sales(s, pipeline.sales)
                await s.commit()
            log.info(
                "цикл: листингов %s, оценено %s, пушей %s, продано %s, ошибок %s",
                res.listings,
                res.evaluated,
                res.notified,
                res.sold_marked,
                len(res.errors),
            )
            if once:
                return 0
            await asyncio.sleep(settings.listings_poll_interval_s)
    finally:
        await bot.session.close()
