"""Runtime registry for proxy executors and shared state.

This module instantiates long-lived objects like caches, browser session
managers and runtime executors. It exposes a helper :func:`get_runtime`
function that maps execution mode names to their corresponding runtime
instance. This centralises the shared dependencies used by the proxy
server.
"""

from __future__ import annotations

from .cache import TTLCache
from .browser.site_cookie_store import SiteCookieStore
from .browser.session_manager import BrowserSessionManager
from .runtimes.http_runtime import HttpRuntime
from .runtimes.browser_runtime import BrowserRuntime
from .runtimes.hybrid_runtime import HybridRuntime

# Instantiate shared state objects
cache = TTLCache()
cookie_store = SiteCookieStore()
browser_session_manager = BrowserSessionManager()

# Instantiate runtimes
http_runtime = HttpRuntime(cache=cache, cookie_store=cookie_store)
browser_runtime = BrowserRuntime(session_manager=browser_session_manager, cookie_store=cookie_store)
hybrid_runtime = HybridRuntime(browser_runtime=browser_runtime, http_runtime=http_runtime)


def get_runtime(mode: str):
    """Return the appropriate runtime instance for the given mode.

    Parameters:
        mode: One of ``"http"``, ``"browser"``, or ``"hybrid"``. Any other
            value will raise a ``ValueError``.

    Returns:
        The corresponding runtime instance.
    """
    if mode == "http":
        return http_runtime
    if mode == "browser":
        return browser_runtime
    if mode == "hybrid":
        return hybrid_runtime
    raise ValueError(f"Unsupported execution mode: {mode}")


def reset_runtime_state() -> None:
    """Clear cache and cookie state shared by runtime instances."""
    cache.clear()
    cookie_store.clear_all()
