from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from playerstats_proxy.core.config import Settings
from playerstats_proxy.models.schemas import TopResponse
from playerstats_proxy.services.aggregate_service import compute_aggregate
from playerstats_proxy.services.playerstats_client import PlayerStatsClient
from playerstats_proxy.services.top_service import build_top
from playerstats_proxy.models.schemas import SectionTopResponse
from playerstats_proxy.services.top_service import build_section_top

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/moss", tags=["top"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_playerstats_client(request: Request) -> PlayerStatsClient:
    return request.app.state.playerstats_client


@router.get("/top/section/{section}", response_model=SectionTopResponse)
async def top_by_section_total(
    section: str,
    request: Request,
    limit: int = Query(10, ge=1),
    include_zeros: bool = Query(False),
    settings: Settings = Depends(get_settings),
    client: PlayerStatsClient = Depends(get_playerstats_client),
) -> SectionTopResponse:
    limit = min(limit, settings.max_limit)

    cached_players = request.app.state.players_cache.get()
    if cached_players is None:
        try:
            players = await client.fetch_players()
        except httpx.HTTPError as e:
            logger.exception("Upstream HTTP error while fetching players")
            raise HTTPException(status_code=502, detail=f"Upstream HTTP error: {type(e).__name__}") from e
        except ValueError as e:
            logger.exception("Upstream payload error")
            raise HTTPException(status_code=502, detail=str(e)) from e

        request.app.state.players_cache.set(players)
        request.app.state.maxima_cache.clear()
        request.app.state.aggregate_cache.clear()
        cached_players = players

    cached_aggregate = request.app.state.aggregate_cache.get()
    if cached_aggregate is None:
        cached_aggregate = compute_aggregate(cached_players)
        request.app.state.aggregate_cache.set(cached_aggregate)

    # Total de la section = somme des totaux de tous ses stat_key
    section_map = cached_aggregate.get(section) or {}
    total_value = sum(int(v or 0) for v in section_map.values())

    return build_section_top(
        players=cached_players,
        section=section,
        limit=limit,
        include_zeros=include_zeros,
        total_value=max(0, int(total_value)),
    )

@router.get("/top/{stat_key}/{section}", response_model=TopResponse)
async def top_by_section(
    stat_key: str,
    section: str,
    request: Request,
    limit: int = Query(10, ge=1),
    include_zeros: bool = Query(False),
    settings: Settings = Depends(get_settings),
    client: PlayerStatsClient = Depends(get_playerstats_client),
) -> TopResponse:
    limit = min(limit, settings.max_limit)

    # Cache joueurs
    cached_players = request.app.state.players_cache.get()
    if cached_players is None:
        try:
            players = await client.fetch_players()
        except httpx.HTTPError as e:
            logger.exception("Upstream HTTP error while fetching players")
            raise HTTPException(status_code=502, detail=f"Upstream HTTP error: {type(e).__name__}") from e
        except ValueError as e:
            logger.exception("Upstream payload error")
            raise HTTPException(status_code=502, detail=str(e)) from e

        request.app.state.players_cache.set(players)
        request.app.state.maxima_cache.clear()
        request.app.state.aggregate_cache.clear()
        cached_players = players

    # Cache agrégat
    cached_aggregate = request.app.state.aggregate_cache.get()
    if cached_aggregate is None:
        cached_aggregate = compute_aggregate(cached_players)
        request.app.state.aggregate_cache.set(cached_aggregate)

    total_value = int((cached_aggregate.get(section) or {}).get(stat_key, 0) or 0)
    total_value = max(0, total_value)

    return build_top(
        players=cached_players,
        section=section,
        stat_key=stat_key,
        limit=limit,
        include_zeros=include_zeros,
        total_value=total_value,
    )


