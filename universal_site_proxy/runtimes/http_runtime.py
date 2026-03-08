"""HTTP runtime implementation.

This runtime dispatches API operations via ``httpx.AsyncClient`` to remote
HTTP endpoints. It supports caching of GET requests, header and query
parameter filtering and body forwarding for methods like POST or PUT.
Cookies may be injected from the site cookie store to support hybrid
authentication flows.
"""

from __future__ import annotations

import json
from typing import Any, Dict
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, Response

from ..cache import TTLCache
from ..models import OperationSpec
from ..browser.site_cookie_store import SiteCookieStore
from .base import Runtime


class HttpRuntime(Runtime):
    def __init__(
        self,
        cache: TTLCache,
        cookie_store: SiteCookieStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.cache = cache
        self.cookie_store = cookie_store
        self.client = client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    def _render_path(self, template: str, params: Dict[str, Any]) -> str:
        path = template
        for k, v in params.items():
            path = path.replace(f"{{{k}}}", str(v))
        return path

    def _filter_query(self, request: Request, allowed: list[str] | None) -> Dict[str, str]:
        q = dict(request.query_params)
        if allowed is None:
            return q
        return {k: v for k, v in q.items() if k in allowed}

    def _filter_headers(self, request: Request, allowed: list[str]) -> Dict[str, str]:
        incoming = dict(request.headers)
        allowed_set = {h.lower() for h in allowed}
        return {k: v for k, v in incoming.items() if k.lower() in allowed_set}

    async def _parse_body(self, request: Request) -> Any:
        ct = request.headers.get("content-type", "")
        if "application/json" in ct:
            try:
                return await request.json()
            except Exception:
                return None
        raw = await request.body()
        return raw if raw else None

    async def execute(
        self,
        site: str,
        op: OperationSpec,
        base_url: str,
        request: Request,
        path_params: Dict[str, Any],
    ) -> Any:
        if not op.path:
            raise HTTPException(status_code=500, detail=f"Operation '{op.name}' has no HTTP path")
        # Build upstream URL
        upstream_path = self._render_path(op.path, path_params)
        upstream_url = f"{base_url.rstrip('/')}{upstream_path}"
        query = self._filter_query(request, op.allowed_query_params)
        headers = self._filter_headers(request, op.allowed_headers)
        # Inject cookies from browser-based login
        site_cookies = self.cookie_store.get(site)
        if site_cookies:
            headers["cookie"] = "; ".join(f"{k}={v}" for k, v in site_cookies.items())
        body = await self._parse_body(request) if op.forward_body else None
        # Build cache key for GET requests with caching enabled
        cache_key = None
        if op.method.upper() == "GET" and op.cache_ttl_sec:
            cache_key = json.dumps({"u": upstream_url, "q": query}, sort_keys=True)
            cached = self.cache.get(cache_key)
            if cached is not None:
                return JSONResponse(content=cached)
        # Dispatch request
        try:
            resp = await self.client.request(
                op.method.upper(),
                upstream_url,
                params=query,
                headers=headers,
                json=body if isinstance(body, dict) else None,
                content=body if isinstance(body, (bytes, bytearray)) else None,
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream request failed: {e}") from e
        content_type = resp.headers.get("content-type", "")
        if resp.status_code >= 400:
            detail: Any = resp.text
            if "application/json" in content_type:
                try:
                    detail = resp.json()
                except Exception:
                    pass
            raise HTTPException(status_code=resp.status_code, detail=detail)
        if "application/json" in content_type:
            try:
                data = resp.json()
            except ValueError as exc:
                raise HTTPException(status_code=502, detail=f"Upstream returned invalid JSON for {upstream_url}") from exc
            if cache_key and op.cache_ttl_sec:
                self.cache.set(cache_key, data, op.cache_ttl_sec)
            return JSONResponse(content=data)
        return Response(
            content=resp.content,
            media_type=content_type or "text/plain",
            status_code=resp.status_code,
        )
