"""Compatibility shim for the assistant AI trace lifecycle module."""

from __future__ import annotations

import sys

from .assistant import ai_trace_lifecycle as _impl

sys.modules[__name__] = _impl
