"""Group network requests by endpoint pattern.

This module defines an :class:`EndpointCluster` that normalizes paths and
clusters requests by HTTP method and normalized path. Numeric IDs and UUIDs
are replaced with placeholders to group similar requests together.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Dict, List, Any


class EndpointCluster:
    """Cluster network requests into endpoint templates."""

    def normalize_path(self, path: str) -> str:
        # Replace UUIDs with {uuid}
        path = re.sub(r"/[0-9a-fA-F-]{36}", "/{uuid}", path)
        # Replace numeric segments with {id}
        path = re.sub(r"/\d+", "/{id}", path)
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        return path

    def cluster(self, records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        endpoints: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            if r["type"] != "request":
                continue
            parsed = urlparse(r["url"])
            normalized = self.normalize_path(parsed.path)
            key = f"{r['method']} {normalized}"
            endpoints.setdefault(key, []).append(r)
        return endpoints
