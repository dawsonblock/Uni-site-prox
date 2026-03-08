"""Specification loading and validation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import yaml
from pydantic import ValidationError

from .models import SiteSpec


DEFAULT_EXTERNAL_SPEC_DIR_NAME = "api_maps"


class SpecError(RuntimeError):
    """Base exception for spec validation and loading errors."""


class SpecValidationError(SpecError):
    """Raised when a spec file fails structural or semantic validation."""


class DuplicateSiteError(SpecError):
    """Raised when two files declare the same site identifier."""


def get_bundled_spec_dir() -> Path:
    """Return the package directory containing bundled example specs."""
    return Path(__file__).resolve().parent / "api_maps"


def get_default_external_spec_dir() -> Path:
    """Return the default external spec directory for local use."""
    return Path.cwd() / DEFAULT_EXTERNAL_SPEC_DIR_NAME


def resolve_spec_dirs(spec_dir: str | Path | None = None) -> List[Path]:
    """Return the ordered list of directories to search for spec files."""
    bundled = get_bundled_spec_dir().resolve()
    external = Path(spec_dir).expanduser().resolve() if spec_dir else get_default_external_spec_dir().resolve()
    directories: List[Path] = [bundled]
    if external != bundled:
        directories.append(external)
    return directories


def _iter_spec_files(directory: Path) -> Iterable[Path]:
    yaml_files = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))
    yield from sorted(yaml_files)


def _load_yaml_file(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise SpecValidationError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SpecValidationError(f"Spec file {path} must contain a top-level mapping.")
    return data


def validate_site_spec(spec: SiteSpec, source: str | Path = "<memory>") -> SiteSpec:
    """Validate semantic constraints that Pydantic alone does not enforce."""
    if not spec.site.strip():
        raise SpecValidationError(f"Spec {source} must define a non-empty site identifier.")
    if not spec.operations:
        raise SpecValidationError(f"Spec {source} must define at least one operation.")

    for operation_name, operation in sorted(spec.operations.items()):
        if operation.name != operation_name:
            raise SpecValidationError(
                f"Spec {source} operation key '{operation_name}' must match its name field '{operation.name}'."
            )
        if operation.execution_mode in {"http", "hybrid"} and not operation.path:
            raise SpecValidationError(
                f"Spec {source} operation '{operation_name}' requires a path for {operation.execution_mode} mode."
            )
        if operation.execution_mode == "browser" and not (operation.start_url or operation.browser_actions):
            raise SpecValidationError(
                f"Spec {source} browser operation '{operation_name}' requires start_url or browser_actions."
            )
    return spec


def load_spec_file(path: str | Path) -> SiteSpec:
    """Load and validate a single YAML spec file."""
    spec_path = Path(path).expanduser().resolve()
    if not spec_path.exists():
        raise SpecValidationError(f"Spec file {spec_path} does not exist.")
    if not spec_path.is_file():
        raise SpecValidationError(f"Spec path {spec_path} is not a file.")

    data = _load_yaml_file(spec_path)
    try:
        spec = SiteSpec(**data)
    except ValidationError as exc:
        raise SpecValidationError(f"Spec {spec_path} failed model validation: {exc}") from exc
    return validate_site_spec(spec, spec_path)


def load_specs(spec_dir: str | Path | None = None) -> List[SiteSpec]:
    """Load bundled specs plus an optional external directory of specs."""
    specs: List[SiteSpec] = []
    site_sources: dict[str, Path] = {}

    for directory in resolve_spec_dirs(spec_dir):
        if directory.exists() and not directory.is_dir():
            raise SpecValidationError(f"Spec directory {directory} exists but is not a directory.")
        if not directory.exists():
            continue

        for file in _iter_spec_files(directory):
            spec = load_spec_file(file)
            previous = site_sources.get(spec.site)
            if previous is not None:
                raise DuplicateSiteError(
                    f"Duplicate site '{spec.site}' found in {previous} and {file}. Rename or remove one of them."
                )
            site_sources[spec.site] = file
            specs.append(spec)

    return sorted(specs, key=lambda item: item.site)
