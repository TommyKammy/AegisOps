"""Compatibility shim for the action review chain module."""

from __future__ import annotations

import sys

from .actions.review import action_review_chain as _impl

sys.modules[__name__] = _impl
