from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from universal_site_proxy import registry
from universal_site_proxy.models import OperationSpec
from universal_site_proxy.server import _build_proxy_route, create_app

from .conftest import write_yaml


def test_build_proxy_route_includes_path_parameters():
    route = _build_proxy_route(
        "demo",
        "get_item",
        OperationSpec(name="get_item", method="GET", path="/items/{id}", execution_mode="http"),
    )

    assert route == "/demo/get_item/{id}"


def test_create_app_proxies_external_spec_requests(tmp_path, monkeypatch):
    write_yaml(
        tmp_path / "demo.yaml",
        {
            "site": "demo",
            "base_url": "https://api.example.com",
            "operations": {
                "get_item": {
                    "name": "get_item",
                    "method": "GET",
                    "path": "/items/{id}",
                    "execution_mode": "http",
                    "allowed_query_params": ["q"],
                }
            },
        },
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.example.com/items/123?q=widget"
        return httpx.Response(200, json={"id": 123, "name": "Widget"})

    monkeypatch.setattr(
        registry.http_runtime,
        "client",
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    app = create_app(spec_dir=tmp_path)

    with TestClient(app) as client:
        response = client.get("/demo/get_item/123?q=widget&ignored=true")

    assert response.status_code == 200
    assert response.json() == {"id": 123, "name": "Widget"}
