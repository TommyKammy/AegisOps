"""Compatibility shim for the action review projection module."""

from __future__ import annotations

import sys

from .actions.review import action_review_projection as _impl

sys.modules[__name__] = _impl
