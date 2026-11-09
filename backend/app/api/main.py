"""API для Mini App (PLAN 6). Запуск: `uvicorn app.api.main:app`.

Авторизация — заголовок `Authorization: tma <initData>`, проверка HMAC по токену бота и
`user.id == OWNER_CHAT_ID`. initData не логируется и не передаётся в URL.
Режимы confirm/auto через API не включаются (D-009, Этап 7).
"""

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.auth import InitDataError, TgUser, verify_init_data
from app.bot.handlers import panic
from app.bot.notifier import Notifier
from app.models import Alert, BotState
from app.models import Sale as SaleRow
from app.money import format_ton
from app.pricing.fees import DEFAULT_FEES
from app.rules import repo
from app.rules.filters import DealFilter
from app.settings import LIVE_TRADING_ALLOWED, Settings, get_settings
from app.timeutil import utcnow

MODES_LOCKED = "Режимы confirm/auto недоступны: комиссии не проверены и Этап 7 не разрешён."


class PresetIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    enabled: bool = True
    priority: int = 0
    mode: str = "watch"
    filter: DealFilter = Field(default_factory=DealFilter)


class PresetPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    enabled: bool | None = None
    priority: int | None = None
    mode: str | None = None
    filter: DealFilter | None = None


class StateIn(BaseModel):
    paused: bool | None = None
    panic: bool | None = None


class _NullApi:
    """API-процесс не шлёт сообщения: состояние пишется в БД, бот читает его сам."""

    async def send(self, chat_id, text, markup) -> int:  # pragma: no cover
        raise RuntimeError("API не отправляет сообщения")

    async def edit(self, chat_id, message_id, text, markup) -> None:  # pragma: no cover
        raise RuntimeError("API не редактирует сообщения")


def _preset_out(p: Any) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "enabled": p.enabled,
        "priority": p.priority,
        "mode": p.mode,
        "filter": p.filter,
        "updated_at": p.updated_at.isoformat(),
    }


def _alert_out(a: Alert, full: bool = False) -> dict[str, Any]:
    payload = a.payload or {}
    listing = payload.get("listing", {})
    out = {
        "id": a.id,
        "status": a.status,
        "market": a.market,
        "listing_id": a.listing_id,
        "collection": listing.get("collection"),
        "number": listing.get("number"),
        "model": listing.get("model"),
        "backdrop": listing.get("backdrop"),
        "price_ton": format_ton(a.price_nano),
        "profit_ton": format_ton(a.profit_nano) if a.profit_nano is not None else None,
        "estimate": payload.get("estimate", True),
        "sent_at": a.sent_at.isoformat(),
        "preset_id": a.preset_id,
    }
    if full:
        out["deal"] = payload
    return out


def _check_mode(mode: str | None) -> None:
    if mode is None or mode == "watch":
        return
    if mode not in ("confirm", "auto"):
        raise HTTPException(422, "mode")
    if not LIVE_TRADING_ALLOWED:
        raise HTTPException(409, MODES_LOCKED)


def create_app(settings: Settings, sessions: async_sessionmaker) -> FastAPI:
    app = FastAPI(title="Gift Flipper API", docs_url=None, redoc_url=None, openapi_url=None)
    owner = settings.owner_chat_id
    notifier = Notifier(_NullApi(), sessions)

    async def user(authorization: Annotated[str | None, Header()] = None) -> TgUser:
        if settings.bot_token is None or owner is None:
            raise HTTPException(503, "не заданы BOT_TOKEN/OWNER_CHAT_ID")
        if not authorization or not authorization.startswith("tma "):
            raise HTTPException(401, "нужен Authorization: tma <initData>")
        try:
            u = verify_init_data(authorization[4:], settings.bot_token.get_secret_value())
        except InitDataError as exc:
            raise HTTPException(401, str(exc)) from exc
        if u.id != owner:
            raise HTTPException(403, "доступ только владельцу")
        return u

    async def db() -> AsyncIterator[AsyncSession]:
        async with sessions() as s:
            yield s

    User = Annotated[TgUser, Depends(user)]
    Db = Annotated[AsyncSession, Depends(db)]

    @app.get("/api/me")
    async def me(u: User, s: Db) -> dict[str, Any]:
        st = await s.get(BotState, u.id)
        return {
            "user": {"id": u.id, "first_name": u.first_name},
            "dry_run": settings.dry_run,
            "live_trading_allowed": LIVE_TRADING_ALLOWED,
            "paused": bool(st and st.paused),
            "panic": bool(st and st.panic),
            "fees": {
                m: {
                    "buy_bps": f.buy_bps,
                    "sell_bps": f.sell_bps,
                    "withdraw_ton": format_ton(f.withdraw_nano, 3),
                    "verified": f.verified,
                    "source": f.source,
                }
                for m, f in DEFAULT_FEES.items()
            },
        }

    @app.post("/api/state")
    async def set_state(body: StateIn, u: User) -> dict[str, bool]:
        if body.panic:
            await panic(notifier, sessions, u.id)
        elif body.panic is False:
            await notifier.set_state(u.id, panic=False, paused=False)
        if body.paused is not None and not body.panic:
            await notifier.set_state(u.id, paused=body.paused)
        st = await notifier.state(u.id)
        return {"paused": st.paused, "panic": st.panic}

    @app.get("/api/deals")
    async def deals(
        u: User,
        s: Db,
        limit: int = Query(50, ge=1, le=200),
        before_id: int | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        q = select(Alert).where(Alert.chat_id == u.id)
        if before_id is not None:
            q = q.where(Alert.id < before_id)
        if status:
            q = q.where(Alert.status == status)
        rows = (await s.execute(q.order_by(Alert.id.desc()).limit(limit))).scalars()
        return [_alert_out(a) for a in rows]

    @app.get("/api/deals/stream")
    async def stream(u: User, after_id: int = 0) -> StreamingResponse:
        """SSE через fetch-стрим (EventSource не умеет заголовки, а initData в URL нельзя)."""

        async def gen() -> AsyncIterator[bytes]:
            last = after_id
            for _ in range(900):  # ~30 мин, затем клиент переподключается
                async with sessions() as s:
                    rows = (
                        (
                            await s.execute(
                                select(Alert)
                                .where(Alert.chat_id == u.id, Alert.id > last)
                                .order_by(Alert.id)
                                .limit(50)
                            )
                        )
                        .scalars()
                        .all()
                    )
                for a in rows:
                    last = a.id
                    yield f"event: deal\ndata: {json.dumps(_alert_out(a))}\n\n".encode()
                yield b": keep-alive\n\n"
                await asyncio.sleep(2)

        return StreamingResponse(
            gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
        )

    @app.get("/api/deals/{alert_id}")
    async def deal(alert_id: int, u: User, s: Db) -> dict[str, Any]:
        a = await s.get(Alert, alert_id)
        if a is None or a.chat_id != u.id:
            raise HTTPException(404)
        return _alert_out(a, full=True)

    @app.get("/api/deals/{alert_id}/sales")
    async def deal_sales(alert_id: int, u: User, s: Db, days: int = Query(7, ge=1, le=30)):
        a = await s.get(Alert, alert_id)
        if a is None or a.chat_id != u.id or not a.payload:
            raise HTTPException(404)
        listing = a.payload["listing"]
        q = select(SaleRow).where(
            SaleRow.collection == listing["collection"],
            SaleRow.occurred_at >= utcnow() - timedelta(days=days),
        )
        if listing.get("model"):
            q = q.where(SaleRow.model == listing["model"])
        rows = (await s.execute(q.order_by(SaleRow.occurred_at))).scalars()
        return [
            {
                "market": r.market,
                "price_ton": format_ton(r.price_nano),
                "price_nano": str(r.price_nano),
                "at": r.occurred_at.isoformat(),
            }
            for r in rows
        ]

    @app.get("/api/presets")
    async def presets(u: User, s: Db) -> list[dict[str, Any]]:
        return [_preset_out(p) for p in await repo.list_presets(s, u.id)]

    @app.post("/api/presets", status_code=201)
    async def create(body: PresetIn, u: User, s: Db) -> dict[str, Any]:
        _check_mode(body.mode)
        p = await repo.create_preset(
            s,
            u.id,
            body.name,
            body.filter,
            priority=body.priority,
            enabled=body.enabled,
            mode="watch",
        )
        await s.commit()
        return _preset_out(p)

    @app.patch("/api/presets/{preset_id}")
    async def patch(preset_id: int, body: PresetPatch, u: User, s: Db) -> dict[str, Any]:
        _check_mode(body.mode)
        changes = body.model_dump(exclude_unset=True)
        if "filter" in changes:
            changes["filter"] = body.filter
        p = await repo.update_preset(s, u.id, preset_id, **changes)
        if p is None:
            raise HTTPException(404)
        await s.commit()
        return _preset_out(p)

    @app.delete("/api/presets/{preset_id}", status_code=204)
    async def delete(preset_id: int, u: User, s: Db) -> None:
        if not await repo.delete_preset(s, u.id, preset_id):
            raise HTTPException(404)
        await s.commit()

    return app


def _default_app() -> FastAPI:
    from app.db import make_engine, make_sessionmaker

    return create_app(get_settings(), make_sessionmaker(make_engine()))


def __getattr__(name: str) -> Any:  # ленивый `app` для uvicorn, без побочных эффектов при импорте
    if name == "app":
        return _default_app()
    raise AttributeError(name)
