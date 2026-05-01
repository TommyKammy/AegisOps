"""Compatibility shim for the action review timeline module."""

from __future__ import annotations

import sys

from .actions.review import action_review_timeline as _impl

sys.modules[__name__] = _impl
