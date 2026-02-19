from __future__ import annotations

from datetime import datetime
from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class TopEntry(BaseModel):
    uuid: str
    name: str
    value: int = Field(ge=0)
    section: str
    stat_key: str

    total_value: int = Field(ge=0)
    percent_of_total: float = Field(ge=0, le=100)


class TopResponse(BaseModel):
    section: str
    stat_key: str
    limit: int = Field(ge=1)
    include_zeros: bool
    updated_at: datetime

    total_value: int = Field(ge=0)
    results: list[TopEntry]


class BestStatEntry(BaseModel):
    section: str
    stat_key: str
    value: int = Field(ge=0)
    max_value: int = Field(ge=0)
    winners_count: int = Field(ge=1)
    tied: bool

    total_value: int = Field(ge=0)
    percent_of_total: float = Field(ge=0, le=100)


class BestStatsResponse(BaseModel):
    uuid: str
    name: str
    min_value: int = Field(ge=0)
    include_zeros: bool
    max_results: int = Field(ge=1)
    updated_at: datetime
    results: list[BestStatEntry]


class AggregateStatsResponse(BaseModel):
    players: int = Field(ge=0)
    min_value: int = Field(ge=0)
    limit_per_section: int = Field(ge=0)
    updated_at: datetime
    stats: Dict[str, Dict[str, int]]


class SectionTopEntry(BaseModel):
    uuid: str
    name: str
    value: int = Field(ge=0)
    section: str
    total_value: int = Field(ge=0)
    percent_of_total: float = Field(ge=0, le=100)


class SectionTopResponse(BaseModel):
    section: str
    limit: int = Field(ge=1)
    include_zeros: bool
    updated_at: datetime
    total_value: int = Field(ge=0)
    results: list[SectionTopEntry]
