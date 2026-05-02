"""Compatibility shim for the protected HTTP surface module."""

from __future__ import annotations

import sys

from .api import http_protected_surface as _impl

sys.modules[__name__] = _impl
