"""Запуск бота: `python -m app.bot`. Нужны BOT_TOKEN и OWNER_CHAT_ID в .env.

Только команды/кнопки владельца и итог дня по расписанию. Цикл наблюдения с пушами —
`python -m app.engine --dry-run --live --notify` (после разрешения живых запросов, D-018).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from app.bot.handlers import make_router
from app.bot.notifier import AiogramApi, Notifier
from app.db import make_engine, make_sessionmaker
from app.security import setup_logging
from app.settings import get_settings
from app.timeutil import utcnow

log = logging.getLogger(__name__)


def seconds_until_hour(hour: int) -> float:
    now = utcnow()
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def daily_summary_loop(notifier: Notifier, api: AiogramApi, chat_id: int, hour: int):
    while True:
        await asyncio.sleep(seconds_until_hour(hour))
        await api.send(chat_id, (await notifier.summary(chat_id)).text(), None)


async def main() -> None:
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.types import MenuButtonWebApp, WebAppInfo

    s = get_settings()
    setup_logging(s.log_level)
    if s.bot_token is None or s.owner_chat_id is None:
        raise SystemExit("нужны BOT_TOKEN и OWNER_CHAT_ID в .env")
    bot = Bot(s.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode="HTML"))
    sessions = make_sessionmaker(make_engine())
    api = AiogramApi(bot)
    notifier = Notifier(api, sessions, s.webapp_url)
    dp = Dispatcher()
    dp.include_router(make_router(notifier, sessions, s.owner_chat_id, s.webapp_url))
    if s.webapp_url:
        await bot.set_chat_menu_button(
            chat_id=s.owner_chat_id,
            menu_button=MenuButtonWebApp(text="Gift Flipper", web_app=WebAppInfo(url=s.webapp_url)),
        )
    task = asyncio.create_task(
        daily_summary_loop(notifier, api, s.owner_chat_id, s.daily_summary_hour_utc)
    )
    try:
        await dp.start_polling(bot)
    finally:
        task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
