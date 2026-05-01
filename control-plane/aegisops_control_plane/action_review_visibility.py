"""Compatibility shim for the action review visibility module."""

from __future__ import annotations

import sys

from .actions.review import action_review_visibility as _impl

sys.modules[__name__] = _impl
