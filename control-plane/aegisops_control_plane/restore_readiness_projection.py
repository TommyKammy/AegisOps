"""Compatibility shim for the restore readiness projection module."""

from __future__ import annotations

import sys

from .runtime import restore_readiness_projection as _impl

sys.modules[__name__] = _impl
