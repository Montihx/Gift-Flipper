"""Inline-кнопки. «Купить» — только в режиме confirm (до Этапа 7 не показывается)."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.rules.filters import Mode


class AlertCb(CallbackData, prefix="a"):
    action: str  # skip | buy
    alert_id: int


class ControlCb(CallbackData, prefix="c"):
    action: str  # pause | resume | panic | summary


def deal_keyboard(
    alert_id: int, listing_url: str | None, webapp_url: str | None, mode: Mode
) -> InlineKeyboardMarkup:
    row1: list[InlineKeyboardButton] = []
    if mode == "confirm":
        row1.append(
            InlineKeyboardButton(
                text="Купить", callback_data=AlertCb(action="buy", alert_id=alert_id).pack()
            )
        )
    row1.append(
        InlineKeyboardButton(
            text="Пропустить", callback_data=AlertCb(action="skip", alert_id=alert_id).pack()
        )
    )
    rows = [row1]
    row2: list[InlineKeyboardButton] = []
    if listing_url:
        row2.append(InlineKeyboardButton(text="Открыть на маркете", url=listing_url))
    if webapp_url:
        row2.append(
            InlineKeyboardButton(
                text="Открыть в приложении",
                web_app=WebAppInfo(url=f"{webapp_url.rstrip('/')}/#/alert/{alert_id}"),
            )
        )
    if row2:
        rows.append(row2)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def control_keyboard(paused: bool, webapp_url: str | None) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="▶️ Продолжить" if paused else "⏸ Пауза",
                callback_data=ControlCb(action="resume" if paused else "pause").pack(),
            ),
            InlineKeyboardButton(text="🛑 Panic", callback_data=ControlCb(action="panic").pack()),
        ],
        [InlineKeyboardButton(text="Итог дня", callback_data=ControlCb(action="summary").pack())],
    ]
    if webapp_url:
        rows.insert(
            0, [InlineKeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=webapp_url))]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


EMPTY = InlineKeyboardMarkup(inline_keyboard=[])
