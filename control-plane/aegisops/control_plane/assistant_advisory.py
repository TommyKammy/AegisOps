"""Compatibility shim for the assistant advisory module."""

from __future__ import annotations

import sys

from .assistant import assistant_advisory as _impl

sys.modules[__name__] = _impl
