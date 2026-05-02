"""Compatibility shim for the readiness operability module."""

from __future__ import annotations

import sys

from .runtime import readiness_operability as _impl

sys.modules[__name__] = _impl
