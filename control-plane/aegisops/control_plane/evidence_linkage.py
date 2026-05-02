"""Compatibility shim for the ingestion evidence linkage module."""

from __future__ import annotations

import sys

from .ingestion import evidence_linkage as _impl

sys.modules[__name__] = _impl
