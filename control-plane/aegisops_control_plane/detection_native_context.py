"""Compatibility shim for the ingestion native detection context module."""

from __future__ import annotations

import sys

from .ingestion import detection_native_context as _impl

sys.modules[__name__] = _impl
