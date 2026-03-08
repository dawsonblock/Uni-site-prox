"""Build runnable proxy specs from discovery results."""

from __future__ import annotations

from collections import Counter
import re
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qs, urlparse


class SpecBuilder:
    """Construct a spec dict from captured network activity."""

    def build(
        self,
        site: str,
        endpoints: Dict[str, List[Dict[str, Any]]],
        classified: Dict[str, Dict[str, Any]],
        auth: Dict[str, Any],
        records: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], List[str]]:
        responses_by_url = self._index_responses(records)
        candidate_operations: List[Dict[str, Any]] = []
        warnings: List[str] = []

        for endpoint, request_records in sorted(endpoints.items()):
            endpoint_type = classified.get(endpoint, {}).get("type", "rest")
            if endpoint_type != "rest":
                warnings.append(f"Skipped unsupported {endpoint_type.upper()} endpoint {endpoint}.")
                continue

            first_request = request_records[0]
            parsed = urlparse(first_request["url"])
            matching_responses = self._matching_responses(request_records, responses_by_url)
            if not any(self._is_json_response(response) for response in matching_responses):
                warnings.append(f"Skipped non-JSON endpoint {endpoint}.")
                continue

            method, path = endpoint.split(" ", 1)
            candidate_operations.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "scheme": parsed.scheme,
                    "netloc": parsed.netloc,
                    "allowed_query_params": self._collect_query_params(request_records),
                }
            )

        if not candidate_operations:
            raise ValueError("No REST JSON endpoints were discovered from the captured traffic.")

        base_scheme, base_netloc = self._select_base_host(candidate_operations)
        base_url = f"{base_scheme}://{base_netloc}"
        operations: Dict[str, Dict[str, Any]] = {}
        used_names: set[str] = set()

        for candidate in candidate_operations:
            if (candidate["scheme"], candidate["netloc"]) != (base_scheme, base_netloc):
                warnings.append(
                    f"Skipped endpoint {candidate['method']} {candidate['path']} from alternate host {candidate['netloc']}."
                )
                continue

            name = self._unique_name(self._derive_name(candidate["method"], candidate["path"]), used_names)
            operations[name] = {
                "name": name,
                "method": candidate["method"],
                "path": candidate["path"],
                "execution_mode": "http",
                "allowed_query_params": candidate["allowed_query_params"] or None,
                "allowed_headers": sorted(auth.get("headers", [])),
                "forward_body": candidate["method"] not in {"GET", "HEAD"},
                "cache_ttl_sec": 60 if candidate["method"] == "GET" else None,
                "description": f"Auto-discovered {candidate['method']} {candidate['path']}",
            }

        if not operations:
            raise ValueError(f"No runnable REST JSON endpoints matched the selected base host {base_url}.")

        spec: Dict[str, Any] = {
            "site": site,
            "base_url": base_url,
            "auth": auth if auth.get("type") != "none" or auth.get("headers") or auth.get("cookies") else None,
            "operations": operations,
        }
        return spec, warnings

    def _index_responses(self, records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        responses: Dict[str, List[Dict[str, Any]]] = {}
        for record in records:
            if record["type"] == "response":
                responses.setdefault(record["url"], []).append(record)
        return responses

    def _matching_responses(
        self,
        request_records: List[Dict[str, Any]],
        responses_by_url: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        matches: List[Dict[str, Any]] = []
        for request in request_records:
            matches.extend(responses_by_url.get(request["url"], []))
        return matches

    def _collect_query_params(self, request_records: List[Dict[str, Any]]) -> List[str]:
        params: set[str] = set()
        for request in request_records:
            params.update(parse_qs(urlparse(request["url"]).query).keys())
        return sorted(params)

    def _select_base_host(self, operations: List[Dict[str, Any]]) -> Tuple[str, str]:
        counts = Counter((item["scheme"], item["netloc"]) for item in operations)
        return sorted(counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))[0][0]

    def _is_json_response(self, response: Dict[str, Any]) -> bool:
        content_type = response.get("headers", {}).get("content-type", "").lower()
        if "application/json" in content_type:
            return True
        body = response.get("body", "").strip()
        return body.startswith("{") or body.startswith("[")

    def _derive_name(self, method: str, path: str) -> str:
        segments: List[str] = [method.lower()]
        stripped = path.strip("/")
        if not stripped:
            segments.append("root")
        else:
            for segment in stripped.split("/"):
                if segment.startswith("{") and segment.endswith("}"):
                    segment = f"by_{segment[1:-1]}"
                clean = re.sub(r"[^a-zA-Z0-9]+", "_", segment).strip("_").lower()
                if clean:
                    segments.append(clean)
        return "_".join(segments)

    def _unique_name(self, candidate: str, used_names: set[str]) -> str:
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate

        suffix = 2
        while f"{candidate}_{suffix}" in used_names:
            suffix += 1
        unique_name = f"{candidate}_{suffix}"
        used_names.add(unique_name)
        return unique_name
