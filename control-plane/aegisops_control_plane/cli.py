"""Compatibility shim for the CLI module."""

from __future__ import annotations

import sys

from .api import cli as _impl

sys.modules[__name__] = _impl
