"""Compatibility shim for the live assistant workflow module."""

from __future__ import annotations

import sys

from .assistant import live_assistant_workflow as _impl

sys.modules[__name__] = _impl
