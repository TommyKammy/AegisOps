"""Compatibility shim for the runtime boundary module."""

from __future__ import annotations

import sys

from .runtime import runtime_boundary as _impl

sys.modules[__name__] = _impl
