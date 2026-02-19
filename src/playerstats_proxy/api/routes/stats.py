from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from playerstats_proxy.core.config import Settings
from playerstats_proxy.models.schemas import AggregateStatsResponse
from playerstats_proxy.services.aggregate_service import build_aggregate_response, compute_aggregate
from playerstats_proxy.services.playerstats_client import PlayerStatsClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/moss", tags=["stats"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_playerstats_client(request: Request) -> PlayerStatsClient:
    return request.app.state.playerstats_client


@router.get("/stats", response_model=AggregateStatsResponse)
async def aggregated_stats(
    request: Request,
    min_value: int = Query(1, ge=0),
    limit_per_section: int = Query(0, ge=0),
    settings: Settings = Depends(get_settings),
    client: PlayerStatsClient = Depends(get_playerstats_client),
) -> AggregateStatsResponse:
    # Garde-fou si quelqu'un met un limit gigantesque
    if limit_per_section > 0:
        limit_per_section = min(limit_per_section, settings.max_limit)

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

    # Cache agrégat brut (sans filtres)
    cached_aggregate = request.app.state.aggregate_cache.get()
    if cached_aggregate is None:
        cached_aggregate = compute_aggregate(cached_players)
        request.app.state.aggregate_cache.set(cached_aggregate)

    return build_aggregate_response(
        aggregate=cached_aggregate,
        players_count=len(cached_players),
        min_value=min_value,
        limit_per_section=limit_per_section,
    )
