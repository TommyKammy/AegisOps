"""Canonical namespace bridge for the AegisOps control plane.

The implementation package remains :mod:`aegisops_control_plane`.  This bridge
lets callers validate the future canonical namespace without relocating modules
or breaking legacy imports.
"""

from __future__ import annotations

from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
import importlib
import importlib.util
import sys
from types import ModuleType

import aegisops_control_plane as _legacy_control_plane

_CANONICAL_PREFIX = __name__ + "."
_LEGACY_PREFIX = "aegisops_control_plane."


class _CanonicalControlPlaneAliasLoader(Loader):
    def __init__(self, canonical_name: str, legacy_name: str) -> None:
        self._canonical_name = canonical_name
        self._legacy_name = legacy_name

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        module = importlib.import_module(self._legacy_name)
        sys.modules[self._canonical_name] = module
        return module

    def exec_module(self, module: ModuleType) -> None:
        sys.modules[self._canonical_name] = module


class _CanonicalControlPlaneAliasFinder(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: object | None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if not fullname.startswith(_CANONICAL_PREFIX):
            return None

        legacy_name = _LEGACY_PREFIX + fullname.removeprefix(_CANONICAL_PREFIX)
        legacy_spec = importlib.util.find_spec(legacy_name)
        if legacy_spec is None:
            return None

        return ModuleSpec(
            fullname,
            _CanonicalControlPlaneAliasLoader(fullname, legacy_name),
            is_package=legacy_spec.submodule_search_locations is not None,
        )


def _install_canonical_alias_finder() -> None:
    for finder in sys.meta_path:
        if isinstance(finder, _CanonicalControlPlaneAliasFinder):
            return
    sys.meta_path.insert(0, _CanonicalControlPlaneAliasFinder())


_install_canonical_alias_finder()

for _name in _legacy_control_plane.__all__:
    globals()[_name] = getattr(_legacy_control_plane, _name)

__all__ = list(_legacy_control_plane.__all__)
