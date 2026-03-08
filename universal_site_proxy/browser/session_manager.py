"""Browser session manager using Playwright.

This module provides a high-level interface to manage Playwright browser
instances. It lazily starts the Playwright service and ensures the browser
process is shared across all requests. Each call to :meth:`new_page`
returns a fresh context and page ready for use. Call :meth:`start` during
application startup and :meth:`stop` during shutdown.
"""

from __future__ import annotations

from playwright.async_api import async_playwright


class BrowserSessionManager:
    def __init__(self) -> None:
        self._playwright = None
        self._browser = None

    async def start(self) -> None:
        """Start Playwright and launch a headless browser if not already started."""
        if self._browser is not None:
            return
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
        except Exception as exc:
            self._playwright = None
            self._browser = None
            raise RuntimeError(
                "Failed to start Playwright Chromium. Ensure Playwright is installed and run "
                "'playwright install chromium' if needed."
            ) from exc

    async def stop(self) -> None:
        """Close the browser and stop Playwright service."""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def new_page(self):
        """Create a new browser context and page.

        Returns a tuple of (context, page) so the caller can close the
        context after use.
        """
        await self.start()
        if self._browser is None:
            raise RuntimeError("Browser session manager failed to initialize a Chromium instance.")
        try:
            context = await self._browser.new_context()
            page = await context.new_page()
        except Exception as exc:
            raise RuntimeError("Failed to open a new Playwright browser page.") from exc
        return context, page
