"""Compatibility shim for the action review coordination module."""

from __future__ import annotations

import sys

from .actions.review import action_review_coordination as _impl

sys.modules[__name__] = _impl
