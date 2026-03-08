"""Hybrid runtime implementation.

This runtime combines browser automation with HTTP replay. It runs optional
browser steps to acquire authentication cookies or tokens and then proceeds
to call the HTTP runtime to fetch structured data. This approach
leverages the speed of HTTP replay while handling anti-bot mechanisms or
login flows via the browser.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import Request

from ..models import OperationSpec
from .base import Runtime
from .browser_runtime import BrowserRuntime
from .http_runtime import HttpRuntime


class HybridRuntime(Runtime):
    def __init__(self, browser_runtime: BrowserRuntime, http_runtime: HttpRuntime) -> None:
        self.browser_runtime = browser_runtime
        self.http_runtime = http_runtime

    async def execute(
        self,
        site: str,
        op: OperationSpec,
        base_url: str,
        request: Request,
        path_params: Dict[str, Any],
    ) -> Any:
        # Optionally run browser actions to acquire session/cookies
        if op.browser_actions or op.start_url:
            await self.browser_runtime.execute(site, op, base_url, request, path_params)
        # Then dispatch HTTP request using updated cookies
        return await self.http_runtime.execute(site, op, base_url, request, path_params)
