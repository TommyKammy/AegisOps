"""Compatibility shim for the evidence osquery external evidence module."""

from __future__ import annotations

import sys

from .evidence import external_evidence_osquery as _impl

sys.modules[__name__] = _impl
