"""Browser runtime implementation.

This runtime executes operations entirely via a Playwright browser. It is
appropriate for situations where data is only available in the DOM or when
the remote site implements non-replayable anti-bot measures. The runtime
supports optional extraction of page contents as JSON, text or raw HTML.
"""

from __future__ import annotations

import json
from typing import Any, Dict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from ..models import OperationSpec
from ..browser.session_manager import BrowserSessionManager
from ..browser.action_runner import BrowserActionRunner
from ..browser.site_cookie_store import SiteCookieStore
from .base import Runtime


class BrowserRuntime(Runtime):
    def __init__(self, session_manager: BrowserSessionManager, cookie_store: SiteCookieStore) -> None:
        self.session_manager = session_manager
        self.cookie_store = cookie_store
        self.runner = BrowserActionRunner()

    async def _persist_cookies(self, site: str, context) -> None:
        cookies = await context.cookies()
        cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
        self.cookie_store.set(site, cookie_dict)

    async def execute(
        self,
        site: str,
        op: OperationSpec,
        base_url: str,
        request: Request,
        path_params: Dict[str, Any],
    ) -> Any:
        if not op.start_url and not op.browser_actions:
            raise HTTPException(status_code=500, detail=f"Browser op '{op.name}' missing start_url/browser_actions")
        query = dict(request.query_params)
        context = None
        try:
            context, page = await self.session_manager.new_page()
            if op.start_url:
                await page.goto(op.start_url)
            # Execute provided browser actions
            await self.runner.run(page, op.browser_actions, query)
            # Extract page content according to spec
            if op.extract_as == "html":
                html = await page.content()
                await self._persist_cookies(site, context)
                return Response(content=html, media_type="text/html")
            if op.extract_as == "text":
                selector = op.extract_selector or "body"
                text = await page.locator(selector).inner_text()
                await self._persist_cookies(site, context)
                return PlainTextResponse(text)
            if op.extract_as == "json":
                selector = op.extract_selector or "body"
                text = await page.locator(selector).inner_text()
                try:
                    data = json.loads(text)
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"Failed to parse browser output as JSON: {e}") from e
                await self._persist_cookies(site, context)
                return JSONResponse(content=data)
            raise HTTPException(status_code=500, detail=f"Unsupported extract_as '{op.extract_as}'")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Browser execution failed for operation '{site}:{op.name}': {exc}",
            ) from exc
        finally:
            if context is not None:
                await context.close()
