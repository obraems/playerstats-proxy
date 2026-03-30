from __future__ import annotations

import httpx


class PlayerStatsClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str, players_path: str) -> None:
        self._client = http_client
        self._base_url = base_url.rstrip("/")
        self._players_path = players_path if players_path.startswith("/") else f"/{players_path}"

    async def fetch_players(self) -> list[dict]:
        # Récupère la liste complète des joueurs via /moss/players
        url = f"{self._base_url}{self._players_path}"
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()

        # Vérifie que la réponse est bien un objet contenant la clé "players"
        if not isinstance(data, dict):
            raise ValueError("Upstream returned unexpected payload (expected object).")

        players = data.get("players")
        if not isinstance(players, list):
            raise ValueError("Upstream returned unexpected payload (expected 'players' list).")

        return players
