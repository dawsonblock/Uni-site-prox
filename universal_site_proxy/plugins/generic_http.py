"""Generic HTTP plugin.

This plugin currently inherits directly from the base Plugin class and
performs no additional processing. It is provided as a placeholder for
future extensions where generic HTTP behaviour might be augmented.
"""

from .base import Plugin


class GenericHttpPlugin(Plugin):
    """Default plugin for HTTP operations (no-op)."""
    pass
