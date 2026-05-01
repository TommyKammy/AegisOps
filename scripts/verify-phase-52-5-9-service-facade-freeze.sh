#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
package_root="${repo_root}/control-plane/aegisops_control_plane"
service_path="${package_root}/service.py"
baseline_path="${repo_root}/docs/maintainability-hotspot-baseline.txt"
boundary_doc="${repo_root}/docs/control-plane-service-internal-boundaries.md"

if [[ ! -f "${service_path}" ]]; then
  echo "Missing service facade file: control-plane/aegisops_control_plane/service.py" >&2
  exit 1
fi

if [[ ! -f "${baseline_path}" ]]; then
  echo "Missing maintainability hotspot baseline: docs/maintainability-hotspot-baseline.txt" >&2
  exit 1
fi

if [[ ! -f "${boundary_doc}" ]]; then
  echo "Missing service boundary document: docs/control-plane-service-internal-boundaries.md" >&2
  exit 1
fi

required_doc_terms=(
  "## 11. Phase 52.5 Facade Freeze And Package Import Rule"
  'No new implementation-heavy behavior belongs in `service.py` after Phase 52.5.'
  "Internal control-plane modules must import moved implementation owners from their domain packages"
  "Compatibility shims are for public or legacy callers, not for package-internal dependency direction."
  "bash scripts/verify-phase-52-5-9-service-facade-freeze.sh"
)

for required in "${required_doc_terms[@]}"; do
  if ! grep -Fq -- "${required}" "${boundary_doc}"; then
    echo "Missing Phase 52.5.9 service facade freeze guidance in docs/control-plane-service-internal-boundaries.md: ${required}" >&2
    exit 1
  fi
done

export PHASE52_5_9_REPO_ROOT="${repo_root}"
export PHASE52_5_9_PACKAGE_ROOT="${package_root}"
export PHASE52_5_9_SERVICE_PATH="${service_path}"
export PHASE52_5_9_BASELINE_PATH="${baseline_path}"

python3 - <<'PY'
from __future__ import annotations

import ast
import os
import pathlib
import sys

repo_root = pathlib.Path(os.environ["PHASE52_5_9_REPO_ROOT"])
package_root = pathlib.Path(os.environ["PHASE52_5_9_PACKAGE_ROOT"])
service_path = pathlib.Path(os.environ["PHASE52_5_9_SERVICE_PATH"])
baseline_path = pathlib.Path(os.environ["PHASE52_5_9_BASELINE_PATH"])

expected_baseline = {
    "path": "control-plane/aegisops_control_plane/service.py",
    "max_lines": "1393",
    "max_effective_lines": "1241",
    "max_facade_methods": "95",
    "facade_class": "AegisOpsControlPlaneService",
    "adr_exception": "ADR-0003",
    "phase": "50.13.5",
    "issue": "#1035",
}

legacy_owner_modules = {
    "aegisops_control_plane.ai_trace_lifecycle": "aegisops_control_plane.assistant.ai_trace_lifecycle",
    "aegisops_control_plane.assistant_advisory": "aegisops_control_plane.assistant.assistant_advisory",
    "aegisops_control_plane.assistant_context": "aegisops_control_plane.assistant.assistant_context",
    "aegisops_control_plane.assistant_provider": "aegisops_control_plane.assistant.assistant_provider",
    "aegisops_control_plane.live_assistant_workflow": "aegisops_control_plane.assistant.live_assistant_workflow",
    "aegisops_control_plane.audit_export": "aegisops_control_plane.reporting.audit_export",
    "aegisops_control_plane.pilot_reporting_export": "aegisops_control_plane.reporting.pilot_reporting_export",
    "aegisops_control_plane.action_review_chain": "aegisops_control_plane.actions.review.action_review_chain",
    "aegisops_control_plane.action_review_coordination": "aegisops_control_plane.actions.review.action_review_coordination",
    "aegisops_control_plane.action_review_index": "aegisops_control_plane.actions.review.action_review_index",
    "aegisops_control_plane.action_review_inspection": "aegisops_control_plane.actions.review.action_review_inspection",
    "aegisops_control_plane.action_review_path_health": "aegisops_control_plane.actions.review.action_review_path_health",
    "aegisops_control_plane.action_review_projection": "aegisops_control_plane.actions.review.action_review_projection",
    "aegisops_control_plane.action_review_timeline": "aegisops_control_plane.actions.review.action_review_timeline",
    "aegisops_control_plane.action_review_visibility": "aegisops_control_plane.actions.review.action_review_visibility",
    "aegisops_control_plane.action_review_write_surface": "aegisops_control_plane.actions.review.action_review_write_surface",
    "aegisops_control_plane.action_lifecycle_write_coordinator": "aegisops_control_plane.actions.action_lifecycle_write_coordinator",
    "aegisops_control_plane.action_policy": "aegisops_control_plane.actions.action_policy",
    "aegisops_control_plane.action_receipt_validation": "aegisops_control_plane.actions.action_receipt_validation",
    "aegisops_control_plane.action_reconciliation_orchestration": "aegisops_control_plane.actions.action_reconciliation_orchestration",
    "aegisops_control_plane.execution_coordinator": "aegisops_control_plane.actions.execution_coordinator",
    "aegisops_control_plane.execution_coordinator_action_requests": "aegisops_control_plane.actions.execution_coordinator_action_requests",
    "aegisops_control_plane.execution_coordinator_delegation": "aegisops_control_plane.actions.execution_coordinator_delegation",
    "aegisops_control_plane.execution_coordinator_reconciliation": "aegisops_control_plane.actions.execution_coordinator_reconciliation",
    "aegisops_control_plane.runtime_boundary": "aegisops_control_plane.runtime.runtime_boundary",
    "aegisops_control_plane.readiness_contracts": "aegisops_control_plane.runtime.readiness_contracts",
    "aegisops_control_plane.readiness_operability": "aegisops_control_plane.runtime.readiness_operability",
    "aegisops_control_plane.restore_readiness": "aegisops_control_plane.runtime.restore_readiness",
    "aegisops_control_plane.restore_readiness_projection": "aegisops_control_plane.runtime.restore_readiness_projection",
    "aegisops_control_plane.restore_readiness_backup_restore": "aegisops_control_plane.runtime.restore_readiness_backup_restore",
    "aegisops_control_plane.runtime_restore_readiness_diagnostics": "aegisops_control_plane.runtime.runtime_restore_readiness_diagnostics",
    "aegisops_control_plane.service_snapshots": "aegisops_control_plane.runtime.service_snapshots",
    "aegisops_control_plane.operations": "aegisops_control_plane.runtime.operations",
    "aegisops_control_plane.cli": "aegisops_control_plane.api.cli",
    "aegisops_control_plane.entrypoint_support": "aegisops_control_plane.api.entrypoint_support",
    "aegisops_control_plane.http_surface": "aegisops_control_plane.api.http_surface",
    "aegisops_control_plane.http_protected_surface": "aegisops_control_plane.api.http_protected_surface",
    "aegisops_control_plane.http_runtime_surface": "aegisops_control_plane.api.http_runtime_surface",
    "aegisops_control_plane.detection_lifecycle": "aegisops_control_plane.ingestion.detection_lifecycle",
    "aegisops_control_plane.detection_lifecycle_helpers": "aegisops_control_plane.ingestion.detection_lifecycle_helpers",
    "aegisops_control_plane.detection_native_context": "aegisops_control_plane.ingestion.detection_native_context",
    "aegisops_control_plane.case_workflow": "aegisops_control_plane.ingestion.case_workflow",
    "aegisops_control_plane.evidence_linkage": "aegisops_control_plane.ingestion.evidence_linkage",
    "aegisops_control_plane.external_evidence_boundary": "aegisops_control_plane.evidence.external_evidence_boundary",
    "aegisops_control_plane.external_evidence_facade": "aegisops_control_plane.evidence.external_evidence_facade",
    "aegisops_control_plane.external_evidence_misp": "aegisops_control_plane.evidence.external_evidence_misp",
    "aegisops_control_plane.external_evidence_osquery": "aegisops_control_plane.evidence.external_evidence_osquery",
    "aegisops_control_plane.external_evidence_endpoint": "aegisops_control_plane.evidence.external_evidence_endpoint",
    "aegisops_control_plane.phase29_shadow_dataset": "aegisops_control_plane.ml_shadow.dataset",
    "aegisops_control_plane.phase29_shadow_scoring": "aegisops_control_plane.ml_shadow.scoring",
    "aegisops_control_plane.phase29_evidently_drift_visibility": "aegisops_control_plane.ml_shadow.drift_visibility",
    "aegisops_control_plane.phase29_mlflow_shadow_model_registry": "aegisops_control_plane.ml_shadow.mlflow_registry",
}

domain_roots = (
    "aegisops_control_plane.actions.",
    "aegisops_control_plane.api.",
    "aegisops_control_plane.assistant.",
    "aegisops_control_plane.evidence.",
    "aegisops_control_plane.ingestion.",
    "aegisops_control_plane.ml_shadow.",
    "aegisops_control_plane.reporting.",
    "aegisops_control_plane.runtime.",
)


def effective_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip() and not line.strip().startswith("#"))


def facade_method_count(text: str, class_name: str) -> int | None:
    tree = ast.parse(text, filename="control-plane/aegisops_control_plane/service.py")
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return sum(
                1
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
    return None


def service_baseline_metadata() -> dict[str, str]:
    for line in baseline_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if parts[0] != expected_baseline["path"]:
            continue
        metadata = {"path": parts[0]}
        for part in parts[1:]:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            metadata[key] = value
        return metadata
    return {}


def module_name_for(path: pathlib.Path) -> str:
    relative = path.relative_to(package_root).with_suffix("")
    return "aegisops_control_plane." + ".".join(relative.parts)


def resolved_import_module(current_module: str, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    package_parts = current_module.split(".")[:-1]
    if node.level > len(package_parts) + 1:
        return None
    anchor = package_parts[: len(package_parts) - node.level + 1]
    if node.module:
        anchor.extend(node.module.split("."))
    return ".".join(anchor)


metadata = service_baseline_metadata()
missing_or_changed = [
    f"{key}={value}"
    for key, value in expected_baseline.items()
    if metadata.get(key) != value
]
if missing_or_changed:
    print(
        "Phase 52.5.9 service facade freeze requires the accepted Phase 50.13.5 "
        "service.py baseline entry; missing or changed fields: "
        + ", ".join(missing_or_changed),
        file=sys.stderr,
    )
    sys.exit(1)

service_text = service_path.read_text(encoding="utf-8")
physical_lines = len(service_text.splitlines())
effective_lines = effective_line_count(service_text)
facade_methods = facade_method_count(service_text, expected_baseline["facade_class"])

if facade_methods is None:
    print(
        "Phase 52.5.9 service facade freeze could not find "
        f"{expected_baseline['facade_class']} in service.py",
        file=sys.stderr,
    )
    sys.exit(1)

limits = {
    "lines": (physical_lines, int(expected_baseline["max_lines"])),
    "effective_lines": (effective_lines, int(expected_baseline["max_effective_lines"])),
    "facade_methods": (facade_methods, int(expected_baseline["max_facade_methods"])),
}
exceeded = [
    f"{name}={actual} exceeds {limit}"
    for name, (actual, limit) in limits.items()
    if actual > limit
]
if exceeded:
    print(
        "Phase 52.5.9 service facade freeze rejects service.py growth beyond the "
        "accepted Phase 50.13.5 ceiling: "
        + ", ".join(exceeded),
        file=sys.stderr,
    )
    sys.exit(1)

violations: list[str] = []
for path in sorted(package_root.rglob("*.py")):
    current_module = module_name_for(path)
    if not current_module.startswith(domain_roots):
        continue
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        print(f"Could not parse {path.relative_to(repo_root).as_posix()}: {exc}", file=sys.stderr)
        sys.exit(1)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        imported_module = resolved_import_module(current_module, node)
        if imported_module in legacy_owner_modules:
            relative_path = path.relative_to(repo_root).as_posix()
            owner = legacy_owner_modules[imported_module]
            violations.append(
                f"{relative_path}:{node.lineno} imports {imported_module}; use {owner}"
            )

if violations:
    print(
        "Phase 52.5.9 internal import cleanup found domain modules importing "
        "compatibility shims:",
        file=sys.stderr,
    )
    for violation in violations:
        print(f"- {violation}", file=sys.stderr)
    sys.exit(1)

print(
    "Phase 52.5.9 service facade freeze passed: "
    f"service.py lines={physical_lines}, effective_lines={effective_lines}, "
    f"AegisOpsControlPlaneService methods={facade_methods}; "
    "domain package internals avoid legacy compatibility shims."
)
PY
