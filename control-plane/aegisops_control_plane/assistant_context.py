"""Compatibility shim for the assistant context module."""

from __future__ import annotations

import sys

from .assistant import assistant_context as _impl

sys.modules[__name__] = _impl
