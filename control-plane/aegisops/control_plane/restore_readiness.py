"""Compatibility shim for the restore readiness module."""

from __future__ import annotations

import sys

from .runtime import restore_readiness as _impl

sys.modules[__name__] = _impl
