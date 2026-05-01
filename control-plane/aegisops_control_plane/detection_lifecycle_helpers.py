"""Compatibility shim for the ingestion detection lifecycle helpers module."""

from __future__ import annotations

import sys

from .ingestion import detection_lifecycle_helpers as _impl

sys.modules[__name__] = _impl
