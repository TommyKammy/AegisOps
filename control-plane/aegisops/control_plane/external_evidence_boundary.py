"""Compatibility shim for the evidence external evidence boundary module."""

from __future__ import annotations

import sys

from .evidence import external_evidence_boundary as _impl

sys.modules[__name__] = _impl
