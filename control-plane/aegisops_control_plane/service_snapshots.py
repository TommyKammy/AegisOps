"""Compatibility shim for the service snapshots module."""

from __future__ import annotations

import sys

from .runtime import service_snapshots as _impl

sys.modules[__name__] = _impl
