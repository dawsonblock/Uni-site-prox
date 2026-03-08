"""GraphQL operation detector.

This module attempts to identify GraphQL operation names in request payloads.
It is used by the discovery engine to label GraphQL requests and may be
expanded in the future to infer query variable schemas.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any


class GraphQLDetector:
    """Extract operation types from GraphQL payloads."""

    def extract_operations(self, requests: List[Dict[str, Any]]) -> List[str]:
        ops: List[str] = []
        for r in requests:
            body = r.get("post_data")
            if not body:
                continue
            try:
                payload = json.loads(body)
            except Exception:
                continue
            query = payload.get("query")
            if not isinstance(query, str):
                continue
            if "query" in query:
                ops.append("query")
            if "mutation" in query:
                ops.append("mutation")
        # Return unique operations
        return list(set(ops))
