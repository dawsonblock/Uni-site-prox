"""Generic browser plugin.

This plugin currently inherits directly from the base Plugin class and
performs no additional processing. It serves as a placeholder for
future browser-specific behaviours such as adding cookies or headers to
browser requests.
"""

from .base import Plugin


class GenericBrowserPlugin(Plugin):
    """Default plugin for browser operations (no-op)."""
    pass
