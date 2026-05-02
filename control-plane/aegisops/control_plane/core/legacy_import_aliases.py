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


def _alias(
    legacy_module: str,
    target_module: str,
    target_family: str,
    owner: str,
) -> LegacyImportAlias:
    return LegacyImportAlias(
        legacy_module=legacy_module,
        target_module=target_module,
        target_family=target_family,
        owner=owner,
    )


LEGACY_IMPORT_ALIASES: dict[str, LegacyImportAlias] = {
    "aegisops_control_plane.action_receipt_validation": _alias(
        "aegisops_control_plane.action_receipt_validation",
        "aegisops_control_plane.actions.action_receipt_validation",
        "actions",
        "actions/action_receipt_validation.py",
    ),
    "aegisops_control_plane.action_review_chain": _alias(
        "aegisops_control_plane.action_review_chain",
        "aegisops_control_plane.actions.review.action_review_chain",
        "actions.review",
        "actions/review/action_review_chain.py",
    ),
    "aegisops_control_plane.action_review_coordination": _alias(
        "aegisops_control_plane.action_review_coordination",
        "aegisops_control_plane.actions.review.action_review_coordination",
        "actions.review",
        "actions/review/action_review_coordination.py",
    ),
    "aegisops_control_plane.action_review_index": _alias(
        "aegisops_control_plane.action_review_index",
        "aegisops_control_plane.actions.review.action_review_index",
        "actions.review",
        "actions/review/action_review_index.py",
    ),
    "aegisops_control_plane.action_review_inspection": _alias(
        "aegisops_control_plane.action_review_inspection",
        "aegisops_control_plane.actions.review.action_review_inspection",
        "actions.review",
        "actions/review/action_review_inspection.py",
    ),
    "aegisops_control_plane.action_review_path_health": _alias(
        "aegisops_control_plane.action_review_path_health",
        "aegisops_control_plane.actions.review.action_review_path_health",
        "actions.review",
        "actions/review/action_review_path_health.py",
    ),
    "aegisops_control_plane.action_review_timeline": _alias(
        "aegisops_control_plane.action_review_timeline",
        "aegisops_control_plane.actions.review.action_review_timeline",
        "actions.review",
        "actions/review/action_review_timeline.py",
    ),
    "aegisops_control_plane.action_review_visibility": _alias(
        "aegisops_control_plane.action_review_visibility",
        "aegisops_control_plane.actions.review.action_review_visibility",
        "actions.review",
        "actions/review/action_review_visibility.py",
    ),
    "aegisops_control_plane.assistant_provider": _alias(
        "aegisops_control_plane.assistant_provider",
        "aegisops_control_plane.assistant.assistant_provider",
        "assistant",
        "assistant/assistant_provider.py",
    ),
    "aegisops_control_plane.audit_export": _alias(
        "aegisops_control_plane.audit_export",
        "aegisops_control_plane.reporting.audit_export",
        "reporting",
        "reporting/audit_export.py",
    ),
    "aegisops_control_plane.detection_lifecycle_helpers": _alias(
        "aegisops_control_plane.detection_lifecycle_helpers",
        "aegisops_control_plane.ingestion.detection_lifecycle_helpers",
        "ingestion",
        "ingestion/detection_lifecycle_helpers.py",
    ),
    "aegisops_control_plane.detection_native_context": _alias(
        "aegisops_control_plane.detection_native_context",
        "aegisops_control_plane.ingestion.detection_native_context",
        "ingestion",
        "ingestion/detection_native_context.py",
    ),
    "aegisops_control_plane.entrypoint_support": _alias(
        "aegisops_control_plane.entrypoint_support",
        "aegisops_control_plane.api.entrypoint_support",
        "api",
        "api/entrypoint_support.py",
    ),
    "aegisops_control_plane.execution_coordinator": _alias(
        "aegisops_control_plane.execution_coordinator",
        "aegisops_control_plane.actions.execution_coordinator",
        "actions",
        "actions/execution_coordinator.py",
    ),
    "aegisops_control_plane.execution_coordinator_delegation": _alias(
        "aegisops_control_plane.execution_coordinator_delegation",
        "aegisops_control_plane.actions.execution_coordinator_delegation",
        "actions",
        "actions/execution_coordinator_delegation.py",
    ),
    "aegisops_control_plane.execution_coordinator_reconciliation": _alias(
        "aegisops_control_plane.execution_coordinator_reconciliation",
        "aegisops_control_plane.actions.execution_coordinator_reconciliation",
        "actions",
        "actions/execution_coordinator_reconciliation.py",
    ),
    "aegisops_control_plane.external_evidence_endpoint": _alias(
        "aegisops_control_plane.external_evidence_endpoint",
        "aegisops_control_plane.evidence.external_evidence_endpoint",
        "evidence",
        "evidence/external_evidence_endpoint.py",
    ),
    "aegisops_control_plane.external_evidence_facade": _alias(
        "aegisops_control_plane.external_evidence_facade",
        "aegisops_control_plane.evidence.external_evidence_facade",
        "evidence",
        "evidence/external_evidence_facade.py",
    ),
    "aegisops_control_plane.external_evidence_misp": _alias(
        "aegisops_control_plane.external_evidence_misp",
        "aegisops_control_plane.evidence.external_evidence_misp",
        "evidence",
        "evidence/external_evidence_misp.py",
    ),
    "aegisops_control_plane.external_evidence_osquery": _alias(
        "aegisops_control_plane.external_evidence_osquery",
        "aegisops_control_plane.evidence.external_evidence_osquery",
        "evidence",
        "evidence/external_evidence_osquery.py",
    ),
    "aegisops_control_plane.operations": _alias(
        "aegisops_control_plane.operations",
        "aegisops_control_plane.runtime.operations",
        "runtime",
        "runtime/operations.py",
    ),
    "aegisops_control_plane.phase29_evidently_drift_visibility": _alias(
        "aegisops_control_plane.phase29_evidently_drift_visibility",
        "aegisops_control_plane.ml_shadow.drift_visibility",
        "ml_shadow",
        "ml_shadow/drift_visibility.py",
    ),
    "aegisops_control_plane.phase29_mlflow_shadow_model_registry": _alias(
        "aegisops_control_plane.phase29_mlflow_shadow_model_registry",
        "aegisops_control_plane.ml_shadow.mlflow_registry",
        "ml_shadow",
        "ml_shadow/mlflow_registry.py",
    ),
    "aegisops_control_plane.phase29_shadow_dataset": _alias(
        "aegisops_control_plane.phase29_shadow_dataset",
        "aegisops_control_plane.ml_shadow.dataset",
        "ml_shadow",
        "ml_shadow/dataset.py",
    ),
    "aegisops_control_plane.phase29_shadow_scoring": _alias(
        "aegisops_control_plane.phase29_shadow_scoring",
        "aegisops_control_plane.ml_shadow.legacy_scoring_adapter",
        "ml_shadow",
        "ml_shadow/legacy_scoring_adapter.py",
    ),
    "aegisops_control_plane.service_snapshots": _alias(
        "aegisops_control_plane.service_snapshots",
        "aegisops_control_plane.runtime.service_snapshots",
        "runtime",
        "runtime/service_snapshots.py",
    ),
}

RETAINED_COMPATIBILITY_BLOCKERS: dict[str, str] = {
    "aegisops_control_plane.service": "Public facade import path retained under ADR-0003 and ADR-0010.",
    "aegisops_control_plane.models": "Authoritative record model import path remains a root owner.",
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
        target = importlib.import_module(_canonical_module_name(alias.target_module))
        sys.modules[legacy_module] = target
        _bind_legacy_module_to_parent(legacy_module, target)
        canonical_alias = _canonical_module_name(legacy_module)
        if canonical_alias != legacy_module:
            sys.modules[canonical_alias] = target
            _bind_legacy_module_to_parent(canonical_alias, target)
        registered[legacy_module] = target
    return registered


def _canonical_module_name(module_name: str) -> str:
    if module_name == "aegisops_control_plane":
        return "aegisops.control_plane"
    if module_name.startswith("aegisops_control_plane."):
        return "aegisops.control_plane" + module_name.removeprefix(
            "aegisops_control_plane"
        )
    return module_name


def _bind_legacy_module_to_parent(legacy_module: str, target: ModuleType) -> None:
    parent_name, _, child_name = legacy_module.rpartition(".")
    if not parent_name:
        return

    parent_module = sys.modules.get(parent_name)
    if parent_module is None:
        if parent_name == "aegisops_control_plane":
            return
        parent_module = importlib.import_module(_canonical_module_name(parent_name))
        sys.modules[parent_name] = parent_module
    setattr(parent_module, child_name, target)
