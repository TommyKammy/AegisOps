from __future__ import annotations

from dataclasses import dataclass
import importlib
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
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
    "aegisops_control_plane.action_lifecycle_write_coordinator": _alias(
        "aegisops_control_plane.action_lifecycle_write_coordinator",
        "aegisops_control_plane.actions.action_lifecycle_write_coordinator",
        "actions",
        "actions/action_lifecycle_write_coordinator.py",
    ),
    "aegisops_control_plane.action_policy": _alias(
        "aegisops_control_plane.action_policy",
        "aegisops_control_plane.actions.action_policy",
        "actions",
        "actions/action_policy.py",
    ),
    "aegisops_control_plane.action_receipt_validation": _alias(
        "aegisops_control_plane.action_receipt_validation",
        "aegisops_control_plane.actions.action_receipt_validation",
        "actions",
        "actions/action_receipt_validation.py",
    ),
    "aegisops_control_plane.action_reconciliation_orchestration": _alias(
        "aegisops_control_plane.action_reconciliation_orchestration",
        "aegisops_control_plane.actions.action_reconciliation_orchestration",
        "actions",
        "actions/action_reconciliation_orchestration.py",
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
    "aegisops_control_plane.action_review_projection": _alias(
        "aegisops_control_plane.action_review_projection",
        "aegisops_control_plane.actions.review.action_review_projection",
        "actions.review",
        "actions/review/action_review_projection.py",
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
    "aegisops_control_plane.action_review_write_surface": _alias(
        "aegisops_control_plane.action_review_write_surface",
        "aegisops_control_plane.actions.review.action_review_write_surface",
        "actions.review",
        "actions/review/action_review_write_surface.py",
    ),
    "aegisops_control_plane.ai_trace_lifecycle": _alias(
        "aegisops_control_plane.ai_trace_lifecycle",
        "aegisops_control_plane.assistant.ai_trace_lifecycle",
        "assistant",
        "assistant/ai_trace_lifecycle.py",
    ),
    "aegisops_control_plane.assistant_advisory": _alias(
        "aegisops_control_plane.assistant_advisory",
        "aegisops_control_plane.assistant.assistant_advisory",
        "assistant",
        "assistant/assistant_advisory.py",
    ),
    "aegisops_control_plane.assistant_context": _alias(
        "aegisops_control_plane.assistant_context",
        "aegisops_control_plane.assistant.assistant_context",
        "assistant",
        "assistant/assistant_context.py",
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
    "aegisops_control_plane.case_workflow": _alias(
        "aegisops_control_plane.case_workflow",
        "aegisops_control_plane.ingestion.case_workflow",
        "ingestion",
        "ingestion/case_workflow.py",
    ),
    "aegisops_control_plane.cli": _alias(
        "aegisops_control_plane.cli",
        "aegisops_control_plane.api.cli",
        "api",
        "api/cli.py",
    ),
    "aegisops_control_plane.detection_lifecycle": _alias(
        "aegisops_control_plane.detection_lifecycle",
        "aegisops_control_plane.ingestion.detection_lifecycle",
        "ingestion",
        "ingestion/detection_lifecycle.py",
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
    "aegisops_control_plane.evidence_linkage": _alias(
        "aegisops_control_plane.evidence_linkage",
        "aegisops_control_plane.ingestion.evidence_linkage",
        "ingestion",
        "ingestion/evidence_linkage.py",
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
    "aegisops_control_plane.execution_coordinator_action_requests": _alias(
        "aegisops_control_plane.execution_coordinator_action_requests",
        "aegisops_control_plane.actions.execution_coordinator_action_requests",
        "actions",
        "actions/execution_coordinator_action_requests.py",
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
    "aegisops_control_plane.external_evidence_boundary": _alias(
        "aegisops_control_plane.external_evidence_boundary",
        "aegisops_control_plane.evidence.external_evidence_boundary",
        "evidence",
        "evidence/external_evidence_boundary.py",
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
    "aegisops_control_plane.http_protected_surface": _alias(
        "aegisops_control_plane.http_protected_surface",
        "aegisops_control_plane.api.http_protected_surface",
        "api",
        "api/http_protected_surface.py",
    ),
    "aegisops_control_plane.http_runtime_surface": _alias(
        "aegisops_control_plane.http_runtime_surface",
        "aegisops_control_plane.api.http_runtime_surface",
        "api",
        "api/http_runtime_surface.py",
    ),
    "aegisops_control_plane.http_surface": _alias(
        "aegisops_control_plane.http_surface",
        "aegisops_control_plane.api.http_surface",
        "api",
        "api/http_surface.py",
    ),
    "aegisops_control_plane.live_assistant_workflow": _alias(
        "aegisops_control_plane.live_assistant_workflow",
        "aegisops_control_plane.assistant.live_assistant_workflow",
        "assistant",
        "assistant/live_assistant_workflow.py",
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
    "aegisops_control_plane.pilot_reporting_export": _alias(
        "aegisops_control_plane.pilot_reporting_export",
        "aegisops_control_plane.reporting.pilot_reporting_export",
        "reporting",
        "reporting/pilot_reporting_export.py",
    ),
    "aegisops_control_plane.readiness_contracts": _alias(
        "aegisops_control_plane.readiness_contracts",
        "aegisops_control_plane.runtime.readiness_contracts",
        "runtime",
        "runtime/readiness_contracts.py",
    ),
    "aegisops_control_plane.readiness_operability": _alias(
        "aegisops_control_plane.readiness_operability",
        "aegisops_control_plane.runtime.readiness_operability",
        "runtime",
        "runtime/readiness_operability.py",
    ),
    "aegisops_control_plane.restore_readiness": _alias(
        "aegisops_control_plane.restore_readiness",
        "aegisops_control_plane.runtime.restore_readiness",
        "runtime",
        "runtime/restore_readiness.py",
    ),
    "aegisops_control_plane.restore_readiness_backup_restore": _alias(
        "aegisops_control_plane.restore_readiness_backup_restore",
        "aegisops_control_plane.runtime.restore_readiness_backup_restore",
        "runtime",
        "runtime/restore_readiness_backup_restore.py",
    ),
    "aegisops_control_plane.restore_readiness_projection": _alias(
        "aegisops_control_plane.restore_readiness_projection",
        "aegisops_control_plane.runtime.restore_readiness_projection",
        "runtime",
        "runtime/restore_readiness_projection.py",
    ),
    "aegisops_control_plane.runtime_boundary": _alias(
        "aegisops_control_plane.runtime_boundary",
        "aegisops_control_plane.runtime.runtime_boundary",
        "runtime",
        "runtime/runtime_boundary.py",
    ),
    "aegisops_control_plane.runtime_restore_readiness_diagnostics": _alias(
        "aegisops_control_plane.runtime_restore_readiness_diagnostics",
        "aegisops_control_plane.runtime.runtime_restore_readiness_diagnostics",
        "runtime",
        "runtime/runtime_restore_readiness_diagnostics.py",
    ),
    "aegisops_control_plane.service_snapshots": _alias(
        "aegisops_control_plane.service_snapshots",
        "aegisops_control_plane.runtime.service_snapshots",
        "runtime",
        "runtime/service_snapshots.py",
    ),
}

CANONICAL_IMPORT_ALIASES: dict[str, LegacyImportAlias] = {
    legacy_module.replace("aegisops_control_plane", "aegisops.control_plane", 1): _alias(
        legacy_module.replace("aegisops_control_plane", "aegisops.control_plane", 1),
        alias.target_module.replace(
            "aegisops_control_plane", "aegisops.control_plane", 1
        ),
        alias.target_family,
        alias.owner,
    )
    for legacy_module, alias in LEGACY_IMPORT_ALIASES.items()
    if legacy_module
    in {
        "aegisops_control_plane.action_lifecycle_write_coordinator",
        "aegisops_control_plane.action_policy",
        "aegisops_control_plane.action_reconciliation_orchestration",
        "aegisops_control_plane.action_review_projection",
        "aegisops_control_plane.action_review_write_surface",
        "aegisops_control_plane.ai_trace_lifecycle",
        "aegisops_control_plane.assistant_advisory",
        "aegisops_control_plane.assistant_context",
        "aegisops_control_plane.case_workflow",
        "aegisops_control_plane.detection_lifecycle",
        "aegisops_control_plane.evidence_linkage",
        "aegisops_control_plane.execution_coordinator_action_requests",
        "aegisops_control_plane.external_evidence_boundary",
        "aegisops_control_plane.http_protected_surface",
        "aegisops_control_plane.http_runtime_surface",
        "aegisops_control_plane.http_surface",
        "aegisops_control_plane.live_assistant_workflow",
        "aegisops_control_plane.pilot_reporting_export",
        "aegisops_control_plane.readiness_contracts",
        "aegisops_control_plane.readiness_operability",
        "aegisops_control_plane.restore_readiness",
        "aegisops_control_plane.restore_readiness_backup_restore",
        "aegisops_control_plane.restore_readiness_projection",
        "aegisops_control_plane.runtime_boundary",
        "aegisops_control_plane.runtime_restore_readiness_diagnostics",
    }
}

RETAINED_COMPATIBILITY_BLOCKERS: dict[str, str] = {
    "aegisops_control_plane.service": "Public facade import path retained under ADR-0003 and ADR-0010.",
    "aegisops_control_plane.models": "Authoritative record model import path remains a root owner.",
}


class _ImportAliasLoader(Loader):
    def __init__(self, alias_name: str, target_name: str) -> None:
        self._alias_name = alias_name
        self._target_name = target_name

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        target = importlib.import_module(self._target_name)
        sys.modules[self._alias_name] = target
        _bind_module_to_parent(self._alias_name, target)
        return target

    def exec_module(self, module: ModuleType) -> None:
        sys.modules[self._alias_name] = module
        _bind_module_to_parent(self._alias_name, module)


class _ImportAliasFinder(MetaPathFinder):
    def __init__(self, aliases: dict[str, LegacyImportAlias]) -> None:
        self._targets = {
            alias_name: _canonical_module_name(alias.target_module)
            for alias_name, alias in aliases.items()
        }

    def find_spec(
        self,
        fullname: str,
        path: object | None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        target_name = self._targets.get(fullname)
        if target_name is None:
            return None
        return ModuleSpec(fullname, _ImportAliasLoader(fullname, target_name))


def _install_import_alias_finder(aliases: dict[str, LegacyImportAlias]) -> None:
    for index, finder in enumerate(sys.meta_path):
        if isinstance(finder, _ImportAliasFinder):
            sys.meta_path[index] = _ImportAliasFinder(aliases)
            return
    sys.meta_path.insert(0, _ImportAliasFinder(aliases))


def register_legacy_import_aliases(
    aliases: dict[str, LegacyImportAlias] = LEGACY_IMPORT_ALIASES,
) -> dict[str, ModuleType]:
    all_aliases = CANONICAL_IMPORT_ALIASES | aliases
    for canonical_module, alias in CANONICAL_IMPORT_ALIASES.items():
        if canonical_module != alias.legacy_module:
            raise ValueError(
                f"canonical import alias key mismatch: {canonical_module} != {alias.legacy_module}"
            )

    for legacy_module, alias in aliases.items():
        if legacy_module != alias.legacy_module:
            raise ValueError(
                f"legacy import alias key mismatch: {legacy_module} != {alias.legacy_module}"
            )
    _install_import_alias_finder(all_aliases)
    return {
        alias_name: sys.modules[alias_name]
        for alias_name in all_aliases
        if alias_name in sys.modules
    }


def _canonical_module_name(module_name: str) -> str:
    if module_name == "aegisops_control_plane":
        return "aegisops.control_plane"
    if module_name.startswith("aegisops_control_plane."):
        return "aegisops.control_plane" + module_name.removeprefix(
            "aegisops_control_plane"
        )
    return module_name


def _bind_module_to_parent(module_name: str, target: ModuleType) -> None:
    parent_name, _, child_name = module_name.rpartition(".")
    if not parent_name:
        return

    parent_module = sys.modules.get(parent_name)
    if parent_module is None:
        if parent_name == "aegisops_control_plane":
            return
        parent_module = importlib.import_module(_canonical_module_name(parent_name))
        sys.modules[parent_name] = parent_module
    setattr(parent_module, child_name, target)
