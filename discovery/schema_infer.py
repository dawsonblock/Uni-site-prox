"""Simple JSON schema inference.

This module defines a simple mechanism to infer keys of JSON responses. It
returns the set of top-level keys found in the response bodies of captured
responses.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any, AnyStr


class SchemaInfer:
    """Infer top-level keys from JSON response bodies."""

    def infer(self, responses: List[Dict[str, Any]]) -> List[str]:
        schemas: List[List[str]] = []
        for r in responses:
            if r["type"] != "response":
                continue
            body = r.get("body", "")
            try:
                data = json.loads(body)
            except Exception:
                continue
            schemas.append(self._extract_keys(data))
        if schemas:
            # Return the most detailed schema
            return max(schemas, key=len)
        return []

    def _extract_keys(self, obj: Any) -> List[str]:
        if isinstance(obj, dict):
            return sorted(obj.keys())
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            return sorted(obj[0].keys())
        return []
