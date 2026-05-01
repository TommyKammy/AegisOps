"""Compatibility shim for the readiness contracts module."""

from __future__ import annotations

import sys

from .runtime import readiness_contracts as _impl

sys.modules[__name__] = _impl
