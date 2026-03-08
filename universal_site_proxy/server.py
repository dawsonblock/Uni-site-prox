"""FastAPI application for the universal site proxy."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from .models import OperationSpec, SiteSpec
from .registry import browser_session_manager, get_runtime
from .spec_loader import load_specs


def _build_proxy_route(site: str, op_name: str, op: OperationSpec) -> str:
    """Build a route path for a site operation."""
    route = f"/{site}/{op_name}"
    if op.path:
        for segment in op.path.split("/"):
            if segment.startswith("{") and segment.endswith("}"):
                route += f"/{segment}"
    return route


def _register_route(
    app: FastAPI,
    site: str,
    base_url: str,
    op_name: str,
    op: OperationSpec,
    registered: set[tuple[str, str]],
) -> None:
    route = _build_proxy_route(site, op_name, op)
    route_key = (op.method.upper(), route)
    if route_key in registered:
        raise ValueError(f"Route collision detected for {op.method.upper()} {route}.")
    registered.add(route_key)

    async def handler(request: Request) -> Response:
        runtime = get_runtime(op.execution_mode)
        try:
            return await runtime.execute(
                site, op, base_url, request, dict(request.path_params)
            )
        except HTTPException:
            raise
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    app.add_api_route(
        route,
        handler,
        methods=[op.method.upper()],
        name=f"{site}:{op_name}",
        summary=op.description or op_name,
    )


def _register_specs(app: FastAPI, specs: list[SiteSpec]) -> None:
    registered: set[tuple[str, str]] = set()
    for spec in specs:
        for op_name, op in sorted(spec.operations.items()):
            _register_route(app, spec.site, spec.base_url, op_name, op, registered)
    app.state.loaded_specs = specs


def create_app(spec_dir: str | None = None) -> FastAPI:
    """Create a configured FastAPI app."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await browser_session_manager.stop()

    app = FastAPI(title="Universal Site Proxy", lifespan=lifespan)
    specs = load_specs(spec_dir)
    _register_specs(app, specs)

    return app


from fastapi.middleware.cors import CORSMiddleware

app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
