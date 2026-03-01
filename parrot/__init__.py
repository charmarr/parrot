"""Parrot — CI auto-healing for charmarr charms."""

from parrot._engine import parrot
from parrot import _tools  # noqa: F401 — triggers tool registration

__all__ = ["parrot"]
