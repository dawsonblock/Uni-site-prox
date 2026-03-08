"""Browser action runner for Playwright.

This module defines a helper class that executes high-level browser
operations described by the :class:`~universal_site_proxy.models.BrowserAction`
model. It replaces placeholders with query parameters and wraps the common
operations used by the proxy.
"""

from __future__ import annotations

from typing import Dict, List
from playwright.async_api import Page
from ..models import BrowserAction


class BrowserActionRunner:
    """Executes browser actions on a Playwright page."""

    async def run(self, page: Page, actions: List[BrowserAction], query_params: Dict[str, str]) -> None:
        """Execute a sequence of actions using the provided page.

        Parameters:
            page: A Playwright ``Page`` instance.
            actions: A list of :class:`BrowserAction` objects defining the steps to take.
            query_params: A dict of query parameters used to substitute placeholders
                in action values (e.g. ``{query.q}``).
        """
        for action in actions:
            if action.type == "goto":
                url = action.value or ""
                # Substitute placeholders like {query.q}
                for k, v in query_params.items():
                    url = url.replace(f"{{query.{k}}}", str(v))
                await page.goto(url)

            elif action.type == "click" and action.selector:
                # Use wait_for_selector to ensure element is ready
                try:
                    await page.click(action.selector, timeout=2000)
                except Exception:
                    # Ignore click failures; the caller can decide how to handle them
                    pass

            elif action.type == "fill" and action.selector:
                value = action.value or ""
                for k, v in query_params.items():
                    value = value.replace(f"{{query.{k}}}", str(v))
                try:
                    await page.fill(action.selector, value)
                except Exception:
                    pass

            elif action.type == "wait":
                await page.wait_for_timeout(action.ms or 1000)

            elif action.type == "scroll":
                # Scroll by the specified number of pixels; default to 2000
                await page.mouse.wheel(0, action.ms or 2000)
