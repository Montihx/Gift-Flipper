"""Схема фильтра пресета (PLAN 4.1). Хранится как JSON в `presets.filter`.

Пустое поле = без ограничения. Если фильтр требует признак, а данных о нём нет (редкость
у MRKT, монохром без ответа Clue) — сделка НЕ проходит (консервативно).
Деньги — nanoTON, проценты — базисные пункты (1% = 100 bps), редкость — промилле.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.markets.base import Market
from app.pricing.floor import Confidence

Mode = Literal["watch", "confirm", "auto"]


class NumberFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: int | None = Field(default=None, ge=0)
    max: int | None = Field(default=None, ge=0)
    max_distinct_digits: int | None = Field(default=None, ge=1, le=10)  # «красивые» номера

    @model_validator(mode="after")
    def _range(self) -> NumberFilter:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("number.min > number.max")
        return self


class Exclusions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auctions: bool = True
    premarket: bool = True
    locked: bool = True
    bundles: bool = True
    too_good: bool = True  # цена < 25% флора — вероятная ловушка


class DealFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markets: list[Market] = Field(default_factory=list)
    collections: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    backdrops: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    max_model_rarity_pm: int | None = Field(default=None, ge=1, le=1000)
    max_backdrop_rarity_pm: int | None = Field(default=None, ge=1, le=1000)
    max_symbol_rarity_pm: int | None = Field(default=None, ge=1, le=1000)
    number: NumberFilter = Field(default_factory=NumberFilter)
    monochrome_only: bool = False
    min_price_nano: int | None = Field(default=None, ge=0)
    max_price_nano: int | None = Field(default=None, gt=0)
    min_discount_bps: int | None = Field(default=None, ge=0, le=10_000)
    min_profit_nano: int | None = None
    min_roi_bps: int | None = None
    min_comparables: int | None = Field(default=None, ge=1)
    min_confidence: Confidence = "med"
    exclude: Exclusions = Field(default_factory=Exclusions)

    @model_validator(mode="after")
    def _price_range(self) -> DealFilter:
        lo, hi = self.min_price_nano, self.max_price_nano
        if lo is not None and hi is not None and lo > hi:
            raise ValueError("min_price_nano > max_price_nano")
        return self
