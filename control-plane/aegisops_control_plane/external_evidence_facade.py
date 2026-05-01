"""Compatibility shim for the evidence external evidence facade module."""

from __future__ import annotations

import sys

from .evidence import external_evidence_facade as _impl

sys.modules[__name__] = _impl
