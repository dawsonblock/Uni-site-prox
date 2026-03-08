"""Exploration agent for automatic API discovery.

The exploration agent navigates a web page, scans for interactive elements
and triggers actions to elicit network requests that reveal hidden
endpoints. It captures the resulting network traffic via Playwright event
hooks and returns the full list of recorded request/response objects.
"""

from __future__ import annotations

import asyncio
from typing import List, Dict, Any
from playwright.async_api import async_playwright

from .dom_inspector import DOMInspector
from .action_queue import ActionQueue
from .state_tracker import StateTracker


class ExplorerAgent:
    """Interactively explore a web page to discover hidden API calls."""

    def __init__(self) -> None:
        self.inspector = DOMInspector()
        self.queue = ActionQueue()
        self.state = StateTracker()
        self.network_records: List[Dict[str, Any]] = []
        self._pending_response_tasks: List[asyncio.Task] = []

    async def explore(self, url: str, steps: int = 20) -> List[Dict[str, Any]]:
        """Visit a page and perform limited interactive exploration.

        Parameters:
            url: The page to visit.
            steps: Maximum number of actions to perform.

        Returns:
            A list of captured network requests and responses.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.on("request", self._capture_request)
            page.on("response", self._capture_response)
            await page.goto(url)
            for _ in range(steps):
                html = await page.content()
                if self.state.seen_state(html):
                    break
                actions = await self.inspector.scan(page)
                for act in actions:
                    self.queue.add(act)
                action = self.queue.next()
                if not action:
                    break
                if self.state.seen_action(action):
                    continue
                await self._execute_action(page, action)
            if self._pending_response_tasks:
                await asyncio.gather(*self._pending_response_tasks, return_exceptions=True)
            await browser.close()
        return self.network_records

    async def _execute_action(self, page, action: Dict[str, Any]) -> None:
        index = action.get("index", 0)
        if action["type"] == "click":
            try:
                await page.locator(action["selector"]).nth(index).click(timeout=1000)
                await page.wait_for_timeout(1000)
            except Exception:
                pass
        elif action["type"] == "input":
            try:
                await page.locator(action["selector"]).nth(index).fill("test")
                await page.wait_for_timeout(300)
            except Exception:
                pass

    def _capture_request(self, request) -> None:
        self.network_records.append({
            "type": "request",
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data,
        })

    def _capture_response(self, response) -> None:
        self._pending_response_tasks.append(asyncio.create_task(self._record_response(response)))

    async def _record_response(self, response) -> None:
        try:
            body = await response.text()
        except Exception:
            body = ""
        self.network_records.append({
            "type": "response",
            "url": response.url,
            "status": response.status,
            "headers": dict(response.headers),
            "body": body[:2000],
        })
