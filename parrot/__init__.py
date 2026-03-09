"""Parrot — CI auto-healing for charmarr charms."""

from parrot._engine import parrot
from parrot import _lifecycle  # noqa: F401 — triggers hook registration via _runner imports
from parrot import _tools  # noqa: F401 — triggers tool registration

__all__ = ["parrot"]
