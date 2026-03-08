from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pytest
import yaml
from starlette.requests import Request

from universal_site_proxy.registry import reset_runtime_state


@pytest.fixture(autouse=True)
def _reset_runtime_state() -> None:
    reset_runtime_state()
    yield
    reset_runtime_state()


def make_request(
    method: str = "GET",
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json_body: Any | None = None,
    body: bytes | None = None,
) -> Request:
    request_headers = dict(headers or {})
    payload = body or b""
    if json_body is not None:
        payload = json.dumps(json_body).encode("utf-8")
        request_headers.setdefault("content-type", "application/json")

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": urlencode(query or {}, doseq=True).encode("utf-8"),
        "headers": [(key.lower().encode("utf-8"), value.encode("utf-8")) for key, value in request_headers.items()],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }

    async def receive() -> dict[str, Any]:
        nonlocal payload
        chunk = payload
        payload = b""
        return {"type": "http.request", "body": chunk, "more_body": False}

    return Request(scope, receive)


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)
