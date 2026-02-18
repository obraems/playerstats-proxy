from __future__ import annotations

import httpx
from starlette.background import BackgroundTask
from starlette.responses import Response, StreamingResponse


_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _filter_request_headers(headers: dict[str, str]) -> dict[str, str]:
    # Supprime les headers problématiques pour un proxy
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk == "host":
            continue
        if lk == "content-length":
            continue
        out[k] = v
    return out


def _filter_response_headers(headers: httpx.Headers) -> dict[str, str]:
    # Supprime les headers hop-by-hop dans la réponse
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk == "content-length":
            continue
        out[k] = v
    return out


class ReverseProxy:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str) -> None:
        self._client = http_client
        self._base_url = base_url.rstrip("/")

    async def forward(self, method: str, path: str, query: str, headers: dict[str, str], body: bytes) -> Response:
        # Construit l'URL cible
        target_url = f"{self._base_url}{path}"
        if query:
            target_url = f"{target_url}?{query}"

        req_headers = _filter_request_headers(headers)

        # Envoi en streaming pour éviter de charger de gros JSON en RAM
        req = self._client.build_request(method=method, url=target_url, headers=req_headers, content=body)
        upstream_resp = await self._client.send(req, stream=True)

        resp_headers = _filter_response_headers(upstream_resp.headers)
        media_type = upstream_resp.headers.get("content-type")

        # On ferme la réponse upstream à la fin du streaming
        return StreamingResponse(
            upstream_resp.aiter_bytes(),
            status_code=upstream_resp.status_code,
            headers=resp_headers,
            media_type=media_type,
            background=BackgroundTask(upstream_resp.aclose),
        )
