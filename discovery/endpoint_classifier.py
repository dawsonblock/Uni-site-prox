"""Endpoint classifier for discovery engine.

This module analyses captured requests and assigns a simple type label
("rest" or "graphql") based on heuristic inspections of paths and
request bodies.
"""

from __future__ import annotations

import json
from urllib.parse import urlparse
from typing import Dict, List, Any

from .endpoint_cluster import EndpointCluster


class EndpointClassifier:
    """Classify endpoints by transport type."""

    def classify(self, records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        classified: Dict[str, Dict[str, Any]] = {}
        cluster = EndpointCluster()
        for r in records:
            if r["type"] != "request":
                continue
            url = r["url"]
            method = r["method"]
            path = cluster.normalize_path(urlparse(url).path)
            endpoint = f"{method} {path}"
            record_type = "rest"
            # GraphQL endpoints often have "graphql" in the path
            if "graphql" in path.lower():
                record_type = "graphql"
            # Or the request body contains a JSON with a "query" field
            if r.get("post_data"):
                try:
                    payload = json.loads(r["post_data"])
                    if isinstance(payload, dict) and "query" in payload:
                        record_type = "graphql"
                except Exception:
                    pass
            classified.setdefault(endpoint, {"type": record_type, "records": []})
            classified[endpoint]["records"].append(r)
        return classified
