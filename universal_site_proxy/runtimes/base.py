"""Runtime interface definitions.

The proxy uses runtime classes to execute API operations against remote
services. Runtimes encapsulate the different strategies needed for HTTP,
browser-based and hybrid flows. All runtimes must implement the
``execute`` method defined on the abstract base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
from fastapi import Request
from ..models import OperationSpec


class Runtime(ABC):
    """Abstract base class for all runtime executors."""

    @abstractmethod
    async def execute(
        self,
        site: str,
        op: OperationSpec,
        base_url: str,
        request: Request,
        path_params: Dict[str, Any],
    ) -> Any:
        """Execute an operation and return a FastAPI response.

        Implementations must honour the contract of the proxy server and
        accept the same parameters passed from the handler. The returned
        object may be a FastAPI Response or any object accepted by the
        framework as a response body.
        """
        raise NotImplementedError
