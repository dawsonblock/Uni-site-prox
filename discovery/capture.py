"""Network capture using Playwright.

This module defines a :class:`NetworkCapture` class that records request
and response metadata during a browsing session. It uses Playwright to
navigate to a page and logs network traffic for a configurable duration.
"""

from __future__ import annotations

import asyncio
from typing import List, Dict, Any
from playwright.async_api import async_playwright


class NetworkCapture:
    """Record network traffic during a simple page visit."""

    def __init__(self) -> None:
        self.records: List[Dict[str, Any]] = []
        self._pending_response_tasks: List[asyncio.Task] = []

    async def run(self, url: str, duration: int = 10) -> List[Dict[str, Any]]:
        """Navigate to a URL and capture network traffic for a number of seconds.

        Parameters:
            url: The URL to visit.
            duration: How long (in seconds) to capture traffic after page load.

        Returns:
            A list of request/response dictionaries.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.on("request", self._handle_request)
            page.on("response", self._handle_response)
            await page.goto(url)
            # Wait for the page to settle
            await page.wait_for_timeout(duration * 1000)
            if self._pending_response_tasks:
                await asyncio.gather(*self._pending_response_tasks, return_exceptions=True)
            await browser.close()
        return self.records

    def _handle_request(self, request) -> None:
        self.records.append({
            "type": "request",
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data,
        })

    def _handle_response(self, response) -> None:
        self._pending_response_tasks.append(asyncio.create_task(self._record_response(response)))

    async def _record_response(self, response) -> None:
        try:
            body = await response.text()
        except Exception:
            body = ""
        self.records.append({
            "type": "response",
            "url": response.url,
            "status": response.status,
            "headers": dict(response.headers),
            "body": body[:5000],
        })
