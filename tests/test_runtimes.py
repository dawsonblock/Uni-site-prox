from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException

from universal_site_proxy.browser.session_manager import BrowserSessionManager
from universal_site_proxy.browser.site_cookie_store import SiteCookieStore
from universal_site_proxy.cache import TTLCache
from universal_site_proxy.models import OperationSpec
from universal_site_proxy.runtimes.browser_runtime import BrowserRuntime
from universal_site_proxy.runtimes.http_runtime import HttpRuntime
from universal_site_proxy.runtimes.hybrid_runtime import HybridRuntime

from .conftest import make_request


class FakeContext:
    async def cookies(self):
        return [{"name": "session", "value": "abc123"}]

    async def close(self):
        return None


class FakeLocator:
    def __init__(self, text: str) -> None:
        self.text = text

    async def inner_text(self) -> str:
        return self.text


class FakePage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.visited: list[str] = []

    async def goto(self, url: str) -> None:
        self.visited.append(url)

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self.text)


class FakeSessionManager:
    def __init__(self, text: str) -> None:
        self.text = text

    async def new_page(self):
        return FakeContext(), FakePage(self.text)


@pytest.mark.playwright
def test_http_runtime_filters_headers_and_caches_get_requests():
    async def run() -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            assert str(request.url) == "https://api.example.com/items?q=widget"
            assert request.headers["x-api-key"] == "secret"
            assert "x-ignore" not in request.headers
            return httpx.Response(200, json={"ok": True})

        runtime = HttpRuntime(
            cache=TTLCache(),
            cookie_store=SiteCookieStore(),
            client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        operation = OperationSpec(
            name="search_items",
            method="GET",
            path="/items",
            execution_mode="http",
            cache_ttl_sec=60,
            allowed_query_params=["q"],
            allowed_headers=["x-api-key"],
        )

        response_one = await runtime.execute(
            "demo",
            operation,
            "https://api.example.com",
            make_request(query={"q": "widget", "page": "2"}, headers={"x-api-key": "secret", "x-ignore": "no"}),
            {},
        )
        response_two = await runtime.execute(
            "demo",
            operation,
            "https://api.example.com",
            make_request(query={"q": "widget", "page": "2"}, headers={"x-api-key": "secret", "x-ignore": "no"}),
            {},
        )

        assert json.loads(response_one.body) == {"ok": True}
        assert json.loads(response_two.body) == {"ok": True}
        assert calls == 1

    asyncio.run(run())


def test_hybrid_runtime_reuses_browser_cookies_for_http_requests():
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["cookie"] == "session=abc123"
            return httpx.Response(200, json={"source": "http"})

        cookie_store = SiteCookieStore()
        browser_runtime = BrowserRuntime(FakeSessionManager('{"source":"browser"}'), cookie_store)
        http_runtime = HttpRuntime(
            cache=TTLCache(),
            cookie_store=cookie_store,
            client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        hybrid_runtime = HybridRuntime(browser_runtime=browser_runtime, http_runtime=http_runtime)
        operation = OperationSpec(
            name="get_items",
            method="GET",
            path="/items",
            execution_mode="hybrid",
            start_url="https://example.com/login",
            extract_as="json",
        )

        response = await hybrid_runtime.execute(
            "demo",
            operation,
            "https://api.example.com",
            make_request(),
            {},
        )

        assert json.loads(response.body) == {"source": "http"}

    asyncio.run(run())


def test_browser_runtime_smoke_with_data_url():
    async def run() -> None:
        session_manager = BrowserSessionManager()
        runtime = BrowserRuntime(session_manager, SiteCookieStore())
        operation = OperationSpec(
            name="browser_json",
            method="GET",
            execution_mode="browser",
            start_url="data:text/html,%3Cbody%3E%7B%22hello%22%3A%22world%22%7D%3C/body%3E",
            extract_as="json",
        )

        try:
            response = await runtime.execute("demo", operation, "https://api.example.com", make_request(), {})
        except HTTPException as exc:
            if "Failed to start Playwright Chromium" in str(exc.detail):
                pytest.skip(str(exc.detail))
            raise
        finally:
            await session_manager.stop()

        assert json.loads(response.body) == {"hello": "world"}

    asyncio.run(run())
