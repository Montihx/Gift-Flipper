"""Команды и кнопки бота (PLAN 5.1, 5.3, 5.4). Только владелец (`OWNER_CHAT_ID`).

В боте нет меню и настроек (D-001): всё настраивается в Mini App.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.keyboards import AlertCb, ControlCb, control_keyboard
from app.bot.notifier import Notifier
from app.models import Preset

BUY_DISABLED = "Покупки выключены: режим наблюдения (Этап 7 не разрешён)."


async def panic(notifier: Notifier, sessions: async_sessionmaker, chat_id: int) -> None:
    """Panic: всё в watch, пауза уведомлений, стоп исполнения (AGENTS.md §8)."""
    async with sessions() as s:
        await s.execute(update(Preset).where(Preset.owner_chat_id == chat_id).values(mode="watch"))
        await s.commit()
    await notifier.set_state(chat_id, paused=True, panic=True)


def make_router(
    notifier: Notifier, sessions: async_sessionmaker, owner_chat_id: int, webapp_url: str | None
) -> Router:
    router = Router()
    router.message.filter(F.chat.id == owner_chat_id)
    router.callback_query.filter(F.from_user.id == owner_chat_id)

    async def show_controls(message: Message, prefix: str = "") -> None:
        st = await notifier.state(owner_chat_id)
        status = "🛑 Panic" if st.panic else ("⏸ Пауза" if st.paused else "▶️ Наблюдение")
        await message.answer(
            f"{prefix}Gift Flipper — режим наблюдения, покупки выключены.\nСтатус: {status}",
            reply_markup=control_keyboard(st.paused or st.panic, webapp_url),
        )

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await show_controls(message)

    @router.message(Command("pause"))
    async def cmd_pause(message: Message) -> None:
        await notifier.set_state(owner_chat_id, paused=True)
        await show_controls(message)

    @router.message(Command("resume"))
    async def cmd_resume(message: Message) -> None:
        await notifier.set_state(owner_chat_id, paused=False, panic=False)
        await show_controls(message)

    @router.message(Command("panic"))
    async def cmd_panic(message: Message) -> None:
        await panic(notifier, sessions, owner_chat_id)
        await show_controls(message, "🛑 Panic: всё в watch, уведомления остановлены.\n")

    @router.message(Command("summary"))
    async def cmd_summary(message: Message) -> None:
        await message.answer((await notifier.summary(owner_chat_id)).text())

    @router.callback_query(AlertCb.filter(F.action == "skip"))
    async def on_skip(cb: CallbackQuery, callback_data: AlertCb) -> None:
        ok = await notifier.skip(owner_chat_id, callback_data.alert_id)
        await cb.answer("Пропущено" if ok else "Уже неактуально")

    @router.callback_query(AlertCb.filter(F.action == "buy"))
    async def on_buy(cb: CallbackQuery, callback_data: AlertCb) -> None:
        # Ничего не покупаем. Путь к покупке — только execution.spend() на Этапе 7.
        await cb.answer(BUY_DISABLED, show_alert=True)

    @router.callback_query(ControlCb.filter())
    async def on_control(cb: CallbackQuery, callback_data: ControlCb) -> None:
        action = callback_data.action
        if action == "pause":
            await notifier.set_state(owner_chat_id, paused=True)
        elif action == "resume":
            await notifier.set_state(owner_chat_id, paused=False, panic=False)
        elif action == "panic":
            await panic(notifier, sessions, owner_chat_id)
        elif action == "summary":
            await cb.answer()
            if cb.message is not None:
                await cb.message.answer((await notifier.summary(owner_chat_id)).text())
            return
        st = await notifier.state(owner_chat_id)
        if cb.message is not None:
            await cb.message.edit_reply_markup(
                reply_markup=control_keyboard(st.paused or st.panic, webapp_url)
            )
        await cb.answer({"pause": "Пауза", "resume": "Продолжаем", "panic": "Panic"}[action])

    return router
