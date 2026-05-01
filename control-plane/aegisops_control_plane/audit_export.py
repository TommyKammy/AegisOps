"""Compatibility shim for the reporting audit export module."""

from __future__ import annotations

import sys

from .reporting import audit_export as _impl

sys.modules[__name__] = _impl
