"""Command line interface for the Universal Site Proxy."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Iterable

import uvicorn

from discovery.discovery_engine import DiscoveryEngine, DiscoveryReport

from .spec_loader import (
    SpecError,
    get_default_external_spec_dir,
    load_spec_file,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="usp", description="Universal Site Proxy local tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover", help="Discover a site's API surface and write a YAML spec")
    discover_parser.add_argument("url", help="URL to inspect")
    discover_parser.add_argument("--site", required=True, help="Site identifier to use in the generated spec")
    discover_parser.add_argument(
        "--spec-dir",
        help="Directory where generated specs should be written (defaults to ./api_maps)",
    )
    discover_parser.add_argument(
        "--explore",
        action="store_true",
        help="Interact with the page to uncover APIs behind buttons and inputs",
    )
    discover_parser.set_defaults(func=_run_discover)

    validate_parser = subparsers.add_parser("validate-spec", help="Validate a YAML spec file")
    validate_parser.add_argument("spec_path", help="Path to the YAML spec file")
    validate_parser.set_defaults(func=_run_validate_spec)

    serve_parser = subparsers.add_parser("serve", help="Start the local FastAPI proxy")
    serve_parser.add_argument(
        "--spec-dir",
        help="Directory containing discovered specs (defaults to ./api_maps)",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    serve_parser.add_argument("--port", default=8000, type=int, help="Port to bind the server to")
    serve_parser.set_defaults(func=_run_serve)

    return parser


def _print_operations(operations: Iterable[str]) -> None:
    for name in operations:
        print(f"  - {name}")


def _run_discover(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir).expanduser() if args.spec_dir else get_default_external_spec_dir()
    engine = DiscoveryEngine()
    report: DiscoveryReport = asyncio.run(
        engine.discover(
            args.url,
            args.site,
            out_dir=str(spec_dir),
            explore=args.explore,
        )
    )

    print(f"Wrote spec to {report.file_path}")
    print(f"Site: {report.spec['site']}")
    print(f"Base URL: {report.spec['base_url']}")
    print("Operations:")
    _print_operations(sorted(report.spec["operations"].keys()))
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")
    return 0


def _run_validate_spec(args: argparse.Namespace) -> int:
    path = Path(args.spec_path).expanduser()
    spec = load_spec_file(path)
    print(f"Valid spec: {path.resolve()}")
    print(f"Site: {spec.site}")
    print(f"Base URL: {spec.base_url}")
    print("Operations:")
    _print_operations(sorted(spec.operations.keys()))
    return 0


def _run_serve(args: argparse.Namespace) -> int:
    from .server import create_app

    app = create_app(spec_dir=args.spec_dir)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except SpecError as exc:
        print(f"Spec error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
