"""Compatibility shim for the evidence endpoint external evidence module."""

from __future__ import annotations

import sys

from .evidence import external_evidence_endpoint as _impl

sys.modules[__name__] = _impl
