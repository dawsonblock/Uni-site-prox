from __future__ import annotations

from pathlib import Path

from discovery.discovery_engine import DiscoveryReport
from universal_site_proxy import cli

from .conftest import write_yaml


def test_validate_spec_command_prints_summary(tmp_path, capsys):
    spec_path = tmp_path / "demo.yaml"
    write_yaml(
        spec_path,
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

    exit_code = cli.main(["validate-spec", str(spec_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Valid spec:" in output
    assert "demo" in output


def test_discover_command_reports_written_spec(monkeypatch, tmp_path, capsys):
    async def fake_discover(self, url, site_name, out_dir="api_maps", explore=False):
        return DiscoveryReport(
            spec={"site": site_name, "base_url": "https://api.example.com", "operations": {"get_items": {}}},
            file_path=Path(out_dir) / f"{site_name}.yaml",
            warnings=["Skipped unsupported GRAPHQL endpoint POST /graphql."],
            total_records=3,
        )

    monkeypatch.setattr(cli.DiscoveryEngine, "discover", fake_discover)

    exit_code = cli.main(
        ["discover", "https://example.com", "--site", "demo", "--spec-dir", str(tmp_path), "--explore"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Wrote spec to" in output
    assert "Skipped unsupported GRAPHQL endpoint" in output


def test_serve_command_builds_app_and_calls_uvicorn(monkeypatch, tmp_path):
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
    called = {}

    def fake_run(app, host, port):
        called["app"] = app
        called["host"] = host
        called["port"] = port

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)

    exit_code = cli.main(["serve", "--spec-dir", str(tmp_path), "--host", "0.0.0.0", "--port", "9000"])

    assert exit_code == 0
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 9000
    assert [spec.site for spec in called["app"].state.loaded_specs] == ["demo", "dummyjson"]
