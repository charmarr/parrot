"""Parrot — CI auto-healing for charmarr charms."""

import os

os.environ.setdefault("THEOW_LOG_LEVEL", "DEBUG")

from parrot._engine import parrot
from parrot import _lifecycle  # noqa: F401 — triggers hook registration via _runner imports
from parrot import _tools  # noqa: F401 — triggers tool registration

__all__ = ["parrot"]
