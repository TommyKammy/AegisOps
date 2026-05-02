"""Compatibility shim for the action review write surface module."""

from __future__ import annotations

import sys

from .actions.review import action_review_write_surface as _impl

sys.modules[__name__] = _impl
