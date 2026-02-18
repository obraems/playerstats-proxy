from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class TopEntry(BaseModel):
    uuid: str
    name: str
    value: int = Field(ge=0)
    section: str
    stat_key: str


class TopResponse(BaseModel):
    section: str
    stat_key: str
    limit: int = Field(ge=1)
    include_zeros: bool
    updated_at: datetime
    results: list[TopEntry]


class BestStatEntry(BaseModel):
    section: str
    stat_key: str
    value: int = Field(ge=0)
    max_value: int = Field(ge=0)
    winners_count: int = Field(ge=1)
    tied: bool


class BestStatsResponse(BaseModel):
    uuid: str
    name: str
    min_value: int = Field(ge=0)
    include_zeros: bool
    max_results: int = Field(ge=1)
    updated_at: datetime
    results: list[BestStatEntry]