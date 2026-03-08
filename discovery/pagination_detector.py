"""Pagination detector.

Heuristically detect common pagination query parameters such as ``page``,
``limit``, ``offset``, ``cursor`` and ``next`` from captured requests.
"""

from __future__ import annotations

from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs


class PaginationDetector:
    """Detect query parameters used for pagination in captured traffic."""

    COMMON_PARAMS = ["page", "limit", "offset", "cursor", "next", "after"]

    def detect(self, records: List[Dict[str, Any]]) -> Dict[str, str]:
        pagination: Dict[str, str] = {}
        for r in records:
            if r["type"] != "request":
                continue
            parsed = urlparse(r["url"])
            query = parse_qs(parsed.query)
            for key in query:
                if key in self.COMMON_PARAMS:
                    pagination[key] = "query_param"
        return pagination
