from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Request

from playerstats_proxy.services.reverse_proxy import ReverseProxy


router = APIRouter(tags=["upstream"], include_in_schema=False)

_ALL_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


def get_reverse_proxy(request: Request) -> ReverseProxy:
    return request.app.state.reverse_proxy


@router.api_route("/moss/{full_path:path}", methods=_ALL_METHODS)
async def proxy_moss(full_path: str, request: Request) -> object:
    # Forward tout /moss/* qui n'a pas matché une route custom
    proxy = get_reverse_proxy(request)
    try:
        return await proxy.forward(
            method=request.method,
            path=request.url.path,
            query=request.url.query,
            headers=dict(request.headers),
            body=await request.body(),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream proxy error: {type(e).__name__}") from e


@router.api_route("/{full_path:path}", methods=_ALL_METHODS)
async def proxy_everything_else(full_path: str, request: Request) -> object:
    # Forward absolument tout le reste (non /moss), sauf ce que FastAPI a déjà matché (health/docs/etc.)
    proxy = get_reverse_proxy(request)
    try:
        return await proxy.forward(
            method=request.method,
            path=request.url.path,
            query=request.url.query,
            headers=dict(request.headers),
            body=await request.body(),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream proxy error: {type(e).__name__}") from e
