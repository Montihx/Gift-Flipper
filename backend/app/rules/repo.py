"""CRUD пресетов (PLAN 4.2). Валидация фильтра — pydantic `DealFilter`."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Preset
from app.rules.filters import DealFilter, Mode
from app.rules.match import PresetRule
from app.timeutil import utcnow


def to_rule(p: Preset) -> PresetRule:
    return PresetRule(
        p.id,
        p.name,
        p.priority,
        p.enabled,
        p.mode,  # type: ignore[arg-type]
        DealFilter.model_validate(p.filter),
    )


async def create_preset(
    s: AsyncSession,
    owner_chat_id: int,
    name: str,
    flt: DealFilter,
    *,
    priority: int = 0,
    enabled: bool = True,
    mode: Mode = "watch",
) -> Preset:
    now = utcnow()
    p = Preset(
        owner_chat_id=owner_chat_id,
        name=name.strip()[:64],
        enabled=enabled,
        priority=priority,
        mode=mode,
        filter=flt.model_dump(mode="json"),
        created_at=now,
        updated_at=now,
    )
    s.add(p)
    await s.flush()
    return p


async def list_presets(s: AsyncSession, owner_chat_id: int) -> list[Preset]:
    rows = await s.execute(
        select(Preset)
        .where(Preset.owner_chat_id == owner_chat_id)
        .order_by(Preset.priority.desc(), Preset.id)
    )
    return list(rows.scalars())


async def get_preset(s: AsyncSession, owner_chat_id: int, preset_id: int) -> Preset | None:
    p = await s.get(Preset, preset_id)
    return p if p is not None and p.owner_chat_id == owner_chat_id else None


async def update_preset(
    s: AsyncSession, owner_chat_id: int, preset_id: int, **changes: Any
) -> Preset | None:
    p = await get_preset(s, owner_chat_id, preset_id)
    if p is None:
        return None
    allowed = {"name", "enabled", "priority", "mode", "filter"}
    unknown = set(changes) - allowed
    if unknown:
        raise ValueError(f"неизвестные поля: {sorted(unknown)}")
    if "filter" in changes:
        flt = changes["filter"]
        changes["filter"] = (
            flt if isinstance(flt, DealFilter) else DealFilter.model_validate(flt)
        ).model_dump(mode="json")
    if "mode" in changes and changes["mode"] not in ("watch", "confirm", "auto"):
        raise ValueError("mode")
    for k, v in changes.items():
        setattr(p, k, v)
    p.updated_at = utcnow()
    await s.flush()
    return p


async def delete_preset(s: AsyncSession, owner_chat_id: int, preset_id: int) -> bool:
    p = await get_preset(s, owner_chat_id, preset_id)
    if p is None:
        return False
    await s.delete(p)
    await s.flush()
    return True


async def active_rules(s: AsyncSession, owner_chat_id: int) -> list[PresetRule]:
    return [to_rule(p) for p in await list_presets(s, owner_chat_id) if p.enabled]
