"""Compatibility shim for the action review path health module."""

from __future__ import annotations

import sys

from .actions.review import action_review_path_health as _impl

sys.modules[__name__] = _impl
