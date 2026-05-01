"""Compatibility shim for the ingestion detection lifecycle module."""

from __future__ import annotations

import sys

from .ingestion import detection_lifecycle as _impl

sys.modules[__name__] = _impl
