#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
control_plane_root="${repo_root}/control-plane"

if [[ ! -d "${control_plane_root}/aegisops_control_plane" ]]; then
  echo "Missing control-plane package root: control-plane/aegisops_control_plane" >&2
  exit 1
fi

export PHASE52_6_2_REPO_ROOT="${repo_root}"

python3 - <<'PY'
from __future__ import annotations

import ast
import os
from pathlib import Path
import re
import sys

repo_root = Path(os.environ["PHASE52_6_2_REPO_ROOT"]).resolve()
package_root = repo_root / "control-plane" / "aegisops_control_plane"

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

root_shim_names = {module.rsplit(".", 1)[1] for module in legacy_owner_modules}
root_shim_paths = {
    "control-plane/aegisops_control_plane/" + module.rsplit(".", 1)[1] + ".py"
    for module in legacy_owner_modules
}

approved_legacy_python_files = {
    "control-plane/tests/test_phase29_shadow_scoring_validation.py",
    "control-plane/tests/test_service_persistence_action_reconciliation_review_surfaces.py",
    "control-plane/tests/test_service_snapshot_extraction.py",
    "scripts/verify-phase-52-5-2-import-compatibility.sh",
    "scripts/verify-phase-52-5-9-service-facade-freeze.sh",
    "scripts/test-verify-phase-52-5-2-package-scaffolding-and-shim-policy.sh",
    "scripts/test-verify-phase-52-5-9-service-facade-freeze.sh",
    "scripts/verify-phase-52-5-closeout-evaluation.sh",
    "scripts/verify-phase-52-6-2-canonical-domain-imports.sh",
    "scripts/test-verify-phase-52-6-2-canonical-domain-imports.sh",
    "scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh",
    "scripts/test-verify-phase-52-6-3-legacy-import-alias-registry.sh",
    "scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh",
    "scripts/test-verify-phase-52-6-5-retire-phase29-root-filenames.sh",
    "scripts/verify-phase-52-7-4-physical-layout-migration.sh",
    "scripts/test-verify-phase-52-7-3-repo-owned-canonical-namespace.sh",
    "scripts/verify-phase-52-7-5-root-shim-reduction.sh",
    "scripts/test-verify-phase-52-7-5-root-shim-reduction.sh",
    "control-plane/tests/test_phase52_6_3_legacy_import_alias_registry.py",
    "control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py",
    "control-plane/tests/test_phase52_7_5_root_shim_reduction.py",
}

approved_legacy_text_files = {
    "docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md",
    "docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md",
    "docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md",
    "docs/adr/0015-phase-52-6-3-legacy-import-alias-registry.md",
    "docs/control-plane-service-internal-boundaries.md",
    "docs/phase-52-5-closeout-evaluation.md",
    "docs/phase-52-6-closeout-evaluation.md",
} | approved_legacy_python_files


def relative(path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def is_root_shim_file(path: Path) -> bool:
    return relative(path) in root_shim_paths


def python_candidates() -> list[Path]:
    roots = [repo_root / "control-plane", repo_root / "scripts"]
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for pattern in ("*.py", "*.sh"):
            paths.extend(root.rglob(pattern))
    return sorted(set(paths))


def text_candidates() -> list[Path]:
    paths: list[Path] = []
    for root_name, patterns in {
        "docs": ("*.md",),
        "scripts": ("*.sh",),
        ".github": ("*.yml", "*.yaml", "*.md"),
    }.items():
        root = repo_root / root_name
        if not root.exists():
            continue
        for pattern in patterns:
            paths.extend(root.rglob(pattern))
    for extra in ("README.md", "package.json"):
        path = repo_root / extra
        if path.exists():
            paths.append(path)
    return sorted(set(paths))


def import_from_candidates(module: str | None, node: ast.ImportFrom) -> list[str]:
    if module is None:
        return []
    candidates = [module]
    if module == "aegisops_control_plane":
        candidates.extend(f"{module}.{alias.name}" for alias in node.names)
    return candidates


python_violations: list[str] = []
approved_python_hits: set[str] = set()
for path in python_candidates():
    rel = relative(path)
    if rel in approved_legacy_python_files or is_root_shim_file(path):
        approved_python_hits.add(rel)
        continue
    if path.suffix != ".py":
        continue
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    except SyntaxError as exc:
        print(f"Could not parse {rel}: {exc}", file=sys.stderr)
        sys.exit(1)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in legacy_owner_modules:
                    owner = legacy_owner_modules[alias.name]
                    python_violations.append(
                        f"{rel}:{node.lineno} imports {alias.name}; use {owner}"
                    )
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            for candidate in import_from_candidates(node.module, node):
                if candidate in legacy_owner_modules:
                    owner = legacy_owner_modules[candidate]
                    python_violations.append(
                        f"{rel}:{node.lineno} imports {candidate}; use {owner}"
                    )

legacy_text_pattern = re.compile(
    r"\baegisops_control_plane\.(?:"
    + "|".join(re.escape(name.rsplit(".", 1)[1]) for name in sorted(legacy_owner_modules))
    + r")\b"
)
text_violations: list[str] = []
approved_text_hits: set[str] = set()
for path in text_candidates():
    rel = relative(path)
    text = path.read_text(encoding="utf-8")
    if not legacy_text_pattern.search(text):
        continue
    if rel in approved_legacy_text_files:
        approved_text_hits.add(rel)
        continue
    for line_number, line in enumerate(text.splitlines(), start=1):
        if legacy_text_pattern.search(line):
            text_violations.append(
                f"{rel}:{line_number} mentions a root compatibility import path"
            )

violations = python_violations + text_violations
if violations:
    print(
        "Phase 52.6.2 canonical domain import verifier found non-approved "
        "root compatibility shim usage:",
        file=sys.stderr,
    )
    for violation in violations:
        print(f"- {violation}", file=sys.stderr)
    sys.exit(1)

approved_hits = sorted(approved_python_hits | approved_text_hits)
print(
    "Phase 52.6.2 canonical domain import verifier passed: internal callers use "
    "canonical domain imports; approved legacy compatibility usage is limited to "
    + ", ".join(approved_hits)
)
PY
