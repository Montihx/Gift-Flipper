"""Отправка и правка уведомлений (PLAN 5.1–5.3).

- Новая сделка → сообщение и запись в `alerts`.
- Тот же лот с другой ценой → правка существующего сообщения («цена изменилась»), без нового.
- Продажа/снятие → правка в «ПРОДАНО»/«Снято», кнопки убираются (идея topcvetok, D-015).
- Пауза или Panic → новых уведомлений нет; правки статусов продолжаются.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

from aiogram.types import InlineKeyboardMarkup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.keyboards import EMPTY, deal_keyboard
from app.bot.texts import format_deal, format_gone, format_price_changed, format_sold
from app.models import Alert, BotState
from app.money import format_ton
from app.pricing.deal import Deal
from app.pricing.snapshot import deal_snapshot
from app.rules.match import Match
from app.timeutil import utcnow


class BotApi(Protocol):
    async def send(self, chat_id: int, text: str, markup: InlineKeyboardMarkup | None) -> int: ...

    async def edit(
        self, chat_id: int, message_id: int, text: str, markup: InlineKeyboardMarkup | None
    ) -> None: ...


class AiogramApi:
    def __init__(self, bot: Any) -> None:
        self._bot = bot

    async def send(self, chat_id, text, markup) -> int:
        msg = await self._bot.send_message(
            chat_id, text, reply_markup=markup, disable_web_page_preview=True
        )
        return msg.message_id

    async def edit(self, chat_id, message_id, text, markup) -> None:
        from aiogram.exceptions import TelegramBadRequest

        try:
            await self._bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup,
                disable_web_page_preview=True,
            )
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc):
                raise


@dataclass(frozen=True, slots=True)
class Summary:
    alerts: int
    sold: int
    skipped: int
    best_profit_nano: int | None

    def text(self) -> str:
        best = f"{format_ton(self.best_profit_nano)} TON" if self.best_profit_nano else "—"
        return (
            "📊 <b>Итог за 24 ч</b>\n"
            f"Сделок найдено: {self.alerts}\nПродано до нас: {self.sold}\n"
            f"Пропущено: {self.skipped}\nЛучшая оценка прибыли: {best}\n"
            "Покупок: 0 (режим наблюдения)"
        )


class Notifier:
    def __init__(
        self, api: BotApi, sessions: async_sessionmaker, webapp_url: str | None = None
    ) -> None:
        self._api = api
        self._sessions = sessions
        self._webapp = webapp_url

    async def state(self, chat_id: int) -> BotState:
        async with self._sessions() as s:
            st = await s.get(BotState, chat_id)
            if st is None:
                st = BotState(chat_id=chat_id, paused=False, panic=False, updated_at=utcnow())
                s.add(st)
                await s.commit()
            return st

    async def set_state(self, chat_id: int, **flags: bool) -> BotState:
        async with self._sessions() as s:
            st = await s.get(BotState, chat_id) or BotState(
                chat_id=chat_id, paused=False, panic=False, updated_at=utcnow()
            )
            for k, v in flags.items():
                setattr(st, k, v)
            st.updated_at = utcnow()
            s.add(st)
            await s.commit()
            return st

    async def notify(self, chat_id: int, deal: Deal, match: Match) -> Alert | None:
        """Новое сообщение, правка цены или None (пауза/Panic/без изменений)."""
        x = deal.listing
        text = format_deal(deal, match.preset.name)
        async with self._sessions() as s:
            existing = (
                await s.execute(
                    select(Alert).where(
                        Alert.chat_id == chat_id,
                        Alert.market == x.market,
                        Alert.listing_id == x.listing_id,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                if existing.status != "active" or existing.price_nano == x.price_nano:
                    return None
                new_text = format_price_changed(text, existing.price_nano, x.price_nano)
                await self._api.edit(
                    chat_id,
                    existing.message_id,
                    new_text,
                    deal_keyboard(existing.id, x.url, self._webapp, match.effective_mode),
                )
                existing.price_nano, existing.text = x.price_nano, new_text
                existing.payload = deal_snapshot(deal)
                existing.profit_nano, existing.updated_at = deal.profit_nano, utcnow()
                await s.commit()
                return existing
            st = await s.get(BotState, chat_id)
            if st is not None and (st.paused or st.panic):
                return None
            now = utcnow()
            alert = Alert(
                chat_id=chat_id,
                message_id=0,
                market=x.market,
                listing_id=x.listing_id,
                preset_id=match.preset.id,
                price_nano=x.price_nano,
                profit_nano=deal.profit_nano,
                text=text,
                payload=deal_snapshot(deal),
                status="active",
                sent_at=now,
                updated_at=now,
            )
            s.add(alert)
            await s.flush()  # нужен id для callback-кнопок
            alert.message_id = await self._api.send(
                chat_id, text, deal_keyboard(alert.id, x.url, self._webapp, match.effective_mode)
            )
            await s.commit()
            return alert

    async def _close(self, market: str, listing_id: str, status: str, render) -> int:
        async with self._sessions() as s:
            rows = (
                (
                    await s.execute(
                        select(Alert).where(
                            Alert.market == market,
                            Alert.listing_id == listing_id,
                            Alert.status == "active",
                        )
                    )
                )
                .scalars()
                .all()
            )
            for a in rows:
                a.text = render(a.text)
                await self._api.edit(a.chat_id, a.message_id, a.text, EMPTY)
                a.status, a.updated_at = status, utcnow()
            await s.commit()
            return len(rows)

    async def mark_sold(self, market: str, listing_id: str, price_nano: int | None = None) -> int:
        return await self._close(market, listing_id, "sold", lambda t: format_sold(t, price_nano))

    async def mark_gone(self, market: str, listing_id: str) -> int:
        return await self._close(market, listing_id, "gone", format_gone)

    async def skip(self, chat_id: int, alert_id: int) -> bool:
        async with self._sessions() as s:
            a = await s.get(Alert, alert_id)
            if a is None or a.chat_id != chat_id or a.status != "active":
                return False
            a.status, a.updated_at = "skipped", utcnow()
            a.text = "⏭ Пропущено\n" + a.text.removeprefix("🟢 ")
            await self._api.edit(chat_id, a.message_id, a.text, EMPTY)
            await s.commit()
            return True

    async def summary(self, chat_id: int, now: datetime | None = None) -> Summary:
        since = (now or utcnow()) - timedelta(hours=24)
        async with self._sessions() as s:
            rows = (
                await s.execute(
                    select(Alert.status, func.count(), func.max(Alert.profit_nano))
                    .where(Alert.chat_id == chat_id, Alert.sent_at >= since)
                    .group_by(Alert.status)
                )
            ).all()
        by = {r[0]: r[1] for r in rows}
        best = max((r[2] for r in rows if r[2] is not None), default=None)
        return Summary(sum(by.values()), by.get("sold", 0), by.get("skipped", 0), best)
