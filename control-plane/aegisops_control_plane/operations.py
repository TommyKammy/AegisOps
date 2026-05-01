"""Compatibility shim for the operations module."""

from __future__ import annotations

import sys

from .runtime import operations as _impl

sys.modules[__name__] = _impl
