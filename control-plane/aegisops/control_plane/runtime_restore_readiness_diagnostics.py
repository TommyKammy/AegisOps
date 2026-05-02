"""Compatibility shim for the runtime restore readiness diagnostics module."""

from __future__ import annotations

import sys

from .runtime import runtime_restore_readiness_diagnostics as _impl

sys.modules[__name__] = _impl
