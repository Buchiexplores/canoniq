"""CanonIQ — AI-Powered Canonical Mapping Engine.

Map messy source data into trusted canonical models. Local-first by default.
"""

__version__ = "0.2.1"

from canoniq.engine import CanonIQ  # noqa: E402  (must follow __version__ definition)

__all__ = ["CanonIQ", "__version__"]
