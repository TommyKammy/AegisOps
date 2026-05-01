"""Compatibility shim for the entrypoint support module."""

from __future__ import annotations

import sys

from .api import entrypoint_support as _impl

sys.modules[__name__] = _impl
