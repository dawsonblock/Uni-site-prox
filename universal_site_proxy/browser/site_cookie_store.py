"""Simple per-site cookie store.

This module implements a basic dictionary-based cookie store keyed by site name.
It is used by the hybrid runtime to transfer cookies extracted from browser
sessions into the HTTP runtime so subsequent requests remain authenticated.
"""

from __future__ import annotations

from typing import Dict, Any


class SiteCookieStore:
    """Stores cookies per site for reuse across runtime components."""

    def __init__(self) -> None:
        self.cookies: Dict[str, Dict[str, str]] = {}

    def set(self, site: str, cookies: Dict[str, str]) -> None:
        """Store cookies for a given site.

        Parameters:
            site: The site identifier.
            cookies: A mapping of cookie names to values.
        """
        self.cookies[site] = cookies

    def get(self, site: str) -> Dict[str, str] | None:
        """Return stored cookies for the given site, if any."""
        return self.cookies.get(site)

    def clear(self, site: str) -> None:
        """Remove cookies for the given site from the store."""
        if site in self.cookies:
            del self.cookies[site]

    def clear_all(self) -> None:
        """Remove all stored cookies."""
        self.cookies.clear()
