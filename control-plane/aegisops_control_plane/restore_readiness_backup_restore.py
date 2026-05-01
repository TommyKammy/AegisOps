"""Compatibility shim for the restore readiness backup/restore module."""

from __future__ import annotations

import sys

from .runtime import restore_readiness_backup_restore as _impl

sys.modules[__name__] = _impl
