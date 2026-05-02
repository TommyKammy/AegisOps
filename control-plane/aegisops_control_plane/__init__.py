"""Legacy compatibility bridge for the AegisOps control plane."""

from __future__ import annotations

from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
import importlib
import importlib.util
import sys
from types import ModuleType

_LEGACY_PREFIX = __name__ + "."
_CANONICAL_PACKAGE = "aegisops.control_plane"
_CANONICAL_PREFIX = _CANONICAL_PACKAGE + "."


class _LegacyControlPlaneAliasLoader(Loader):
    def __init__(self, legacy_name: str, canonical_name: str) -> None:
        self._legacy_name = legacy_name
        self._canonical_name = canonical_name

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        module = importlib.import_module(self._canonical_name)
        sys.modules[self._legacy_name] = module
        return module

    def exec_module(self, module: ModuleType) -> None:
        sys.modules[self._legacy_name] = module


class _LegacyControlPlaneAliasFinder(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: object | None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if not fullname.startswith(_LEGACY_PREFIX):
            return None

        canonical_name = _CANONICAL_PREFIX + fullname.removeprefix(_LEGACY_PREFIX)
        canonical_spec = importlib.util.find_spec(canonical_name)
        if canonical_spec is None:
            return None

        return ModuleSpec(
            fullname,
            _LegacyControlPlaneAliasLoader(fullname, canonical_name),
            is_package=canonical_spec.submodule_search_locations is not None,
        )


def _install_legacy_alias_finder() -> None:
    for finder in sys.meta_path:
        if isinstance(finder, _LegacyControlPlaneAliasFinder):
            return
    sys.meta_path.insert(0, _LegacyControlPlaneAliasFinder())


_install_legacy_alias_finder()

_canonical_control_plane = importlib.import_module(_CANONICAL_PACKAGE)

for _name in _canonical_control_plane.__all__:
    globals()[_name] = getattr(_canonical_control_plane, _name)

for _module_name, _module in tuple(sys.modules.items()):
    if not _module_name.startswith(_LEGACY_PREFIX):
        continue
    _parent_name, _, _child_name = _module_name.rpartition(".")
    if _parent_name == __name__:
        globals()[_child_name] = _module

__all__ = list(_canonical_control_plane.__all__)
