"""Plugin interface definitions.

Plugins can hook into the execution pipeline by overriding the before and
after hooks. The default implementation simply returns without modifying
inputs or outputs. Plugins can be registered via the ``plugin`` attribute
on :class:`~universal_site_proxy.models.OperationSpec`.
"""

from __future__ import annotations

from abc import ABC
from typing import Any


class Plugin(ABC):
    """Base class for proxy plugins."""

    async def before_execute(self, site: str, op_name: str, request, path_params: dict[str, Any]) -> None:
        """Hook executed before an operation is dispatched to a runtime.

        Subclasses may override this to mutate the request or perform
        additional checks. The default implementation does nothing.
        """
        return None

    async def after_execute(self, site: str, op_name: str, response: Any) -> Any:
        """Hook executed after a runtime returns a response.

        Subclasses may override this to modify the response before it is
        returned to the client. The default implementation returns the
        response unchanged.
        """
        return response
