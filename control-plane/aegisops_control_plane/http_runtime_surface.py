"""Compatibility shim for the runtime HTTP surface module."""

from __future__ import annotations

import sys

from .api import http_runtime_surface as _impl

sys.modules[__name__] = _impl
