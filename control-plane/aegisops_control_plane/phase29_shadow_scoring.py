"""Compatibility shim for the Phase 29 shadow scoring module."""

from __future__ import annotations

import sys

from .ml_shadow import scoring as _impl

sys.modules[__name__] = _impl
