"""Authentication detection for discovery engine.

Inspects request headers to detect whether auth headers or cookies are used.
It returns a dictionary describing the auth type and relevant header names.
"""

from __future__ import annotations

from typing import Dict, List, Any


class AuthDetector:
    """Detect simple auth patterns in captured traffic."""

    AUTH_HEADERS = ["authorization", "x-api-key", "x-auth-token"]
    COOKIE_NAMES = ["session", "auth", "token", "jwt"]

    def detect(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        auth = {
            "type": "none",
            "headers": [],
            "cookies": [],
        }
        for r in records:
            if r["type"] != "request":
                continue
            headers = r.get("headers", {})
            # Check auth headers
            for name, value in headers.items():
                lname = name.lower()
                if lname in self.AUTH_HEADERS:
                    auth["type"] = "header"
                    auth["headers"].append(name)
            # Check cookies
            cookie = headers.get("cookie")
            if cookie:
                lc = cookie.lower()
                for name in self.COOKIE_NAMES:
                    if name in lc:
                        auth["type"] = "cookie"
                        auth["cookies"].append(name)
        # Remove duplicates
        auth["headers"] = list(dict.fromkeys(auth["headers"]))
        auth["cookies"] = list(dict.fromkeys(auth["cookies"]))
        return auth
