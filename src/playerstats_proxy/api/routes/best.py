from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from playerstats_proxy.core.config import Settings
from playerstats_proxy.models.schemas import BestStatsResponse
from playerstats_proxy.services.aggregate_service import compute_aggregate
from playerstats_proxy.services.best_service import build_best_stats, compute_maxima
from playerstats_proxy.services.playerstats_client import PlayerStatsClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/moss", tags=["best"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_playerstats_client(request: Request) -> PlayerStatsClient:
    return request.app.state.playerstats_client


@router.get("/best/{uuid}", response_model=BestStatsResponse)
async def best_stats_for_player(
    uuid: str,
    request: Request,
    min_value: int = Query(1, ge=0),
    include_zeros: bool = Query(False),
    max_results: int = Query(0, ge=0),
    settings: Settings = Depends(get_settings),
    client: PlayerStatsClient = Depends(get_playerstats_client),
) -> BestStatsResponse:
    effective_max_results = settings.max_best_results if max_results <= 0 else min(max_results, settings.max_best_results)

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

    # Cache maxima
    cached_maxima = request.app.state.maxima_cache.get()
    if cached_maxima is None:
        cached_maxima = compute_maxima(cached_players)
        request.app.state.maxima_cache.set(cached_maxima)

    # Cache agrégat
    cached_aggregate = request.app.state.aggregate_cache.get()
    if cached_aggregate is None:
        cached_aggregate = compute_aggregate(cached_players)
        request.app.state.aggregate_cache.set(cached_aggregate)

    try:
        return build_best_stats(
            players=cached_players,
            maxima=cached_maxima,
            aggregate=cached_aggregate,
            player_uuid=uuid,
            min_value=min_value,
            include_zeros=include_zeros,
            max_results=effective_max_results,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Player not found")
