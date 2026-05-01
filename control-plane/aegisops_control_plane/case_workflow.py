"""Compatibility shim for the ingestion case workflow module."""

from __future__ import annotations

import sys

from .ingestion import case_workflow as _impl

sys.modules[__name__] = _impl
