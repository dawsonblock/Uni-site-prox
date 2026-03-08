from __future__ import annotations

import pytest

from universal_site_proxy.spec_loader import DuplicateSiteError, SpecValidationError, load_spec_file, load_specs

from .conftest import write_yaml


def test_load_specs_includes_external_directory(tmp_path):
    write_yaml(
        tmp_path / "demo.yaml",
        {
            "site": "demo",
            "base_url": "https://api.example.com",
            "operations": {
                "get_items": {
                    "name": "get_items",
                    "method": "GET",
                    "path": "/items",
                    "execution_mode": "http",
                }
            },
        },
    )

    specs = load_specs(tmp_path)

    assert [spec.site for spec in specs] == ["demo", "dummyjson"]


def test_load_specs_rejects_duplicate_site_names(tmp_path):
    write_yaml(
        tmp_path / "dummyjson.yaml",
        {
            "site": "dummyjson",
            "base_url": "https://mirror.example.com",
            "operations": {
                "get_items": {
                    "name": "get_items",
                    "method": "GET",
                    "path": "/items",
                    "execution_mode": "http",
                }
            },
        },
    )

    with pytest.raises(DuplicateSiteError):
        load_specs(tmp_path)


def test_load_spec_file_rejects_http_operation_without_path(tmp_path):
    spec_path = tmp_path / "bad.yaml"
    write_yaml(
        spec_path,
        {
            "site": "bad-site",
            "base_url": "https://api.example.com",
            "operations": {
                "broken": {
                    "name": "broken",
                    "method": "GET",
                    "execution_mode": "http",
                }
            },
        },
    )

    with pytest.raises(SpecValidationError):
        load_spec_file(spec_path)
