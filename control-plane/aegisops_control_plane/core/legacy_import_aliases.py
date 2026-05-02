from __future__ import annotations

from dataclasses import dataclass
import importlib
import sys
from types import ModuleType


@dataclass(frozen=True)
class LegacyImportAlias:
    legacy_module: str
    target_module: str
    target_family: str
    owner: str

    def __post_init__(self) -> None:
        for field_name in ("legacy_module", "target_module", "target_family", "owner"):
            if not getattr(self, field_name):
                raise ValueError(f"legacy import alias missing {field_name}")
        if self.legacy_module == self.target_module:
            raise ValueError(
                f"legacy import alias points at itself: {self.legacy_module}"
            )


LEGACY_IMPORT_ALIASES: dict[str, LegacyImportAlias] = {
    "aegisops_control_plane.audit_export": LegacyImportAlias(
        legacy_module="aegisops_control_plane.audit_export",
        target_module="aegisops_control_plane.reporting.audit_export",
        target_family="reporting",
        owner="reporting/audit_export.py",
    ),
}

RETAINED_COMPATIBILITY_BLOCKERS: dict[str, str] = {
    "aegisops_control_plane.service": "Public facade import path retained under ADR-0003 and ADR-0010.",
    "aegisops_control_plane.models": "Authoritative record model import path remains a root owner.",
    "aegisops_control_plane.phase29_shadow_dataset": "Phase29 adapter still needs adapter-specific caller evidence.",
    "aegisops_control_plane.phase29_shadow_scoring": "Phase29 adapter still needs adapter-specific caller evidence.",
    "aegisops_control_plane.phase29_evidently_drift_visibility": "Phase29 adapter still needs adapter-specific caller evidence.",
    "aegisops_control_plane.phase29_mlflow_shadow_model_registry": "Phase29 adapter still needs adapter-specific caller evidence.",
}


def register_legacy_import_aliases(
    aliases: dict[str, LegacyImportAlias] = LEGACY_IMPORT_ALIASES,
) -> dict[str, ModuleType]:
    registered: dict[str, ModuleType] = {}
    for legacy_module, alias in aliases.items():
        if legacy_module != alias.legacy_module:
            raise ValueError(
                f"legacy import alias key mismatch: {legacy_module} != {alias.legacy_module}"
            )
        target = importlib.import_module(alias.target_module)
        sys.modules[legacy_module] = target
        registered[legacy_module] = target
    return registered
