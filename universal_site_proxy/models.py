"""Data models for the universal site proxy.

This module defines Pydantic models used throughout the proxy runtime and
specification loader. These models describe individual API operations and
site-level configuration. Each operation declares its HTTP method, path,
execution mode, caching policies and optional browser automation
instructions when the operation requires a browser flow.
"""

from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


ExecutionMode = Literal["http", "browser", "hybrid"]


class BrowserAction(BaseModel):
    """Represents a single browser automation step.

    Attributes:
        type: The type of action (e.g. ``goto``, ``click``, ``fill``, ``wait``, ``scroll``).
        selector: A CSS selector used for actions that target a specific element.
        value: An optional value used for ``goto`` or ``fill`` actions.
        ms: Milliseconds to wait for wait and scroll actions. For scroll actions this
            represents the scroll distance in pixels.
    """

    type: Literal["goto", "click", "fill", "wait", "scroll"]
    selector: Optional[str] = None
    value: Optional[str] = None
    ms: Optional[int] = None


class OperationSpec(BaseModel):
    """Specification for a single API operation.

    An operation defines how to call a particular endpoint on a remote site. It
    includes the HTTP method, path, caching rules, query and header allowlists
    and optional browser instructions when the operation cannot be replayed
    directly via HTTP.
    """

    name: str
    method: str
    path: Optional[str] = None
    execution_mode: ExecutionMode = "http"
    cache_ttl_sec: Optional[int] = None
    allowed_query_params: Optional[List[str]] = None
    allowed_headers: List[str] = Field(default_factory=list)
    forward_body: bool = False
    description: str = ""

    # Browser/hybrid options
    start_url: Optional[str] = None
    browser_actions: List[BrowserAction] = Field(default_factory=list)
    extract_as: Literal["json", "text", "html"] = "json"
    extract_selector: Optional[str] = None
    plugin: Optional[str] = None


class SiteSpec(BaseModel):
    """Specification for all operations on a given site.

    Attributes:
        site: A short name identifying the site. This name is used in proxy
            routes and should be unique among all loaded specs.
        base_url: The root URL for API requests. For browser based flows this
            can be omitted or left as the home page.
        auth: Optional authentication configuration dictionary. The runtime
            currently does not interpret this but it can be used by plugins.
        operations: A mapping of operation names to their specifications.
    """

    site: str
    base_url: str
    auth: Optional[dict] = None
    operations: dict[str, OperationSpec]
