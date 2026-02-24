from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from playerstats_proxy.api.routes.health import router as health_router
from playerstats_proxy.api.routes.top import router as top_router
from playerstats_proxy.api.routes.best import router as best_router
from playerstats_proxy.api.routes.stats import router as stats_router
from playerstats_proxy.api.routes.players import router as players_router
from playerstats_proxy.api.routes.upstream_proxy import router as upstream_proxy_router
from playerstats_proxy.core.config import Settings
from playerstats_proxy.core.logging import setup_logging
from playerstats_proxy.services.playerstats_client import PlayerStatsClient
from playerstats_proxy.services.reverse_proxy import ReverseProxy
from playerstats_proxy.utils.ttl_cache import TTLCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    settings = Settings()
    timeout = httpx.Timeout(settings.http_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout) as http_client:
        app.state.settings = settings
        app.state.players_cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)
        app.state.maxima_cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)
        app.state.aggregate_cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)

        app.state.playerstats_client = PlayerStatsClient(
            http_client=http_client,
            base_url=settings.upstream_base_url,
            players_path=settings.upstream_players_path,
        )

        # Proxy générique vers l'upstream (ton plugin)
        app.state.reverse_proxy = ReverseProxy(
            http_client=http_client,
            base_url=settings.upstream_base_url,
        )

        yield


app = FastAPI(
    title="PlayerStats Top Proxy",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(top_router)
app.include_router(best_router)
app.include_router(stats_router)
app.include_router(players_router)

# IMPORTANT : à la fin, pour que tes routes custom aient priorité
app.include_router(upstream_proxy_router)
