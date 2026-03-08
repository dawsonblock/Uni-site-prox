"""Top-level discovery engine."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .auth_detector import AuthDetector
from .capture import NetworkCapture
from .endpoint_classifier import EndpointClassifier
from .endpoint_cluster import EndpointCluster
from .explorer.explorer_agent import ExplorerAgent
from .spec_builder import SpecBuilder


@dataclass
class DiscoveryReport:
    """Summary of a discovery run."""

    spec: Dict[str, Any]
    file_path: Path
    warnings: List[str]
    total_records: int


class DiscoveryEngine:
    """Perform automatic discovery of API endpoints for a site."""

    async def discover(
        self,
        url: str,
        site_name: str,
        out_dir: str = "api_maps",
        explore: bool = False,
    ) -> DiscoveryReport:
        """Discover endpoints for the given URL and output a YAML spec."""
        capture = NetworkCapture()
        records = await capture.run(url)
        if explore:
            explorer = ExplorerAgent()
            records.extend(await explorer.explore(url))
        records = self._dedupe_records(records)

        endpoints = EndpointCluster().cluster(records)
        classified = EndpointClassifier().classify(records)
        auth = AuthDetector().detect(records)

        builder = SpecBuilder()
        spec, warnings = builder.build(site_name, endpoints, classified, auth, records)

        out_path = Path(out_dir).expanduser().resolve() / f"{site_name}.yaml"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(spec, handle, sort_keys=False)

        return DiscoveryReport(
            spec=spec,
            file_path=out_path,
            warnings=warnings,
            total_records=len(records),
        )

    def _dedupe_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[str] = set()
        unique_records: List[Dict[str, Any]] = []
        for record in records:
            key = json.dumps(record, sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key)
            unique_records.append(record)
        return unique_records


async def main() -> None:
    engine = DiscoveryEngine()
    report = await engine.discover("https://dummyjson.com/products", "dummyjson_auto")
    print(report.spec)


if __name__ == "__main__":
    asyncio.run(main())
