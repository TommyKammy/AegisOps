"""Compatibility shim for the assistant provider module."""

from __future__ import annotations

import sys

from .assistant import assistant_provider as _impl

sys.modules[__name__] = _impl
