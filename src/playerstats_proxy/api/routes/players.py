from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from playerstats_proxy.core.config import Settings
from playerstats_proxy.models.schemas import BasicPlayerEntry, BasicPlayersResponse
from playerstats_proxy.services.playerstats_client import PlayerStatsClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/moss", tags=["players"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_playerstats_client(request: Request) -> PlayerStatsClient:
    return request.app.state.playerstats_client


@router.get("/players/basic", response_model=BasicPlayersResponse)
async def players_basic(
    request: Request,
    client: PlayerStatsClient = Depends(get_playerstats_client),
) -> BasicPlayersResponse:
    # Récupère les joueurs depuis le cache (ou upstream si cache vide)
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

    # Extrait uniquement les champs utiles pour une liste légère
    result_players: list[BasicPlayerEntry] = []
    for player in cached_players:
        uuid = str(player.get("uuid") or "")
        name = str(player.get("name") or "")
        if not uuid or not name:
            continue

        result_players.append(BasicPlayerEntry(uuid=uuid, name=name))

    # Tri stable et lisible
    result_players.sort(key=lambda p: p.name.lower())

    return BasicPlayersResponse(
        count=len(result_players),
        updated_at=datetime.now(timezone.utc),
        players=result_players,
    )