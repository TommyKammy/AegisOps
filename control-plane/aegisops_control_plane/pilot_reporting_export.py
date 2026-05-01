"""Compatibility shim for the pilot reporting export module."""

from __future__ import annotations

import sys

from .reporting import pilot_reporting_export as _impl

sys.modules[__name__] = _impl
