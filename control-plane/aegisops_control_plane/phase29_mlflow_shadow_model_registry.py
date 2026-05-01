"""Compatibility shim for the Phase 29 MLflow shadow registry module."""

from __future__ import annotations

import sys

from .ml_shadow import mlflow_registry as _impl

sys.modules[__name__] = _impl
