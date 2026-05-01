"""Compatibility shim for the Phase 29 drift visibility module."""

from __future__ import annotations

import sys

from .ml_shadow import drift_visibility as _impl

sys.modules[__name__] = _impl
