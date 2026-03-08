from __future__ import annotations

from discovery.auth_detector import AuthDetector
from discovery.endpoint_classifier import EndpointClassifier
from discovery.endpoint_cluster import EndpointCluster
from discovery.pagination_detector import PaginationDetector
from discovery.schema_infer import SchemaInfer
from discovery.spec_builder import SpecBuilder


def test_endpoint_cluster_normalizes_ids_and_trailing_slashes():
    cluster = EndpointCluster()

    assert cluster.normalize_path("/items/42/") == "/items/{id}"
    assert cluster.normalize_path("/items/123e4567-e89b-12d3-a456-426614174000") == "/items/{uuid}"


def test_endpoint_classifier_marks_graphql_requests():
    records = [
        {
            "type": "request",
            "url": "https://api.example.com/graphql",
            "method": "POST",
            "post_data": '{"query":"{ viewer { id } }"}',
        }
    ]

    classified = EndpointClassifier().classify(records)

    assert classified["POST /graphql"]["type"] == "graphql"


def test_auth_and_pagination_detectors_extract_hints():
    records = [
        {
            "type": "request",
            "url": "https://api.example.com/items?page=2&limit=10",
            "method": "GET",
            "headers": {"authorization": "Bearer token"},
        }
    ]

    auth = AuthDetector().detect(records)
    pagination = PaginationDetector().detect(records)

    assert auth["headers"] == ["authorization"]
    assert pagination == {"page": "query_param", "limit": "query_param"}


def test_schema_infer_returns_most_detailed_shape():
    responses = [
        {"type": "response", "body": '{"id": 1}'},
        {"type": "response", "body": '{"id": 1, "name": "Widget", "price": 9.99}'},
    ]

    assert SchemaInfer().infer(responses) == ["id", "name", "price"]


def test_spec_builder_skips_graphql_and_non_json_endpoints():
    records = [
        {
            "type": "request",
            "url": "https://api.example.com/v1/items?page=1",
            "method": "GET",
            "headers": {"authorization": "Bearer token"},
            "post_data": None,
        },
        {
            "type": "response",
            "url": "https://api.example.com/v1/items?page=1",
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body": '[{"id":1,"name":"Widget"}]',
        },
        {
            "type": "request",
            "url": "https://api.example.com/graphql",
            "method": "POST",
            "headers": {},
            "post_data": '{"query":"{ viewer { id } }"}',
        },
        {
            "type": "response",
            "url": "https://api.example.com/graphql",
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body": '{"data":{"viewer":{"id":"1"}}}',
        },
        {
            "type": "request",
            "url": "https://cdn.example.com/logo.png",
            "method": "GET",
            "headers": {},
            "post_data": None,
        },
        {
            "type": "response",
            "url": "https://cdn.example.com/logo.png",
            "status": 200,
            "headers": {"content-type": "image/png"},
            "body": "",
        },
    ]

    endpoints = EndpointCluster().cluster(records)
    classified = EndpointClassifier().classify(records)
    spec, warnings = SpecBuilder().build(
        "demo",
        endpoints,
        classified,
        {"type": "header", "headers": ["authorization"], "cookies": []},
        records,
    )

    assert spec["base_url"] == "https://api.example.com"
    assert list(spec["operations"].keys()) == ["get_v1_items"]
    assert spec["operations"]["get_v1_items"]["allowed_query_params"] == ["page"]
    assert spec["operations"]["get_v1_items"]["allowed_headers"] == ["authorization"]
    assert "response_keys" not in spec["operations"]["get_v1_items"]
    assert any("GRAPHQL" in warning for warning in warnings)
    assert any("non-JSON" in warning for warning in warnings)
