#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
control_plane_root="${repo_root}/control-plane"
canonical_root="${control_plane_root}/aegisops/control_plane"
legacy_root="${control_plane_root}/aegisops_control_plane"
registry_path="${canonical_root}/core/legacy_import_aliases.py"
test_path="${control_plane_root}/tests/test_phase52_7_5_root_shim_reduction.py"

for required_path in \
  "${canonical_root}/__init__.py" \
  "${canonical_root}/service.py" \
  "${canonical_root}/models.py" \
  "${registry_path}" \
  "${legacy_root}/__init__.py" \
  "${test_path}"; do
  if [[ ! -f "${required_path}" ]]; then
    echo "Missing Phase 52.7.5 root shim reduction path: ${required_path#"${repo_root}/"}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" \
  "${registry_path}" \
  "${test_path}"; then
  echo "Forbidden Phase 52.7.5 root shim reduction: workstation-local absolute path detected" >&2
  exit 1
fi

export PHASE52_7_5_CONTROL_PLANE_ROOT="${control_plane_root}"

python3 - <<'PY'
from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys

control_plane_root = Path(os.environ["PHASE52_7_5_CONTROL_PLANE_ROOT"])
canonical_root = control_plane_root / "aegisops" / "control_plane"
legacy_root = control_plane_root / "aegisops_control_plane"
if str(control_plane_root) not in sys.path:
    sys.path.insert(0, str(control_plane_root))

retained_root_files = {
    "__init__.py",
    "cli.py",
    "config.py",
    "models.py",
    "operator_inspection.py",
    "persistence_lifecycle.py",
    "publishable_paths.py",
    "record_validation.py",
    "reviewed_slice_policy.py",
    "service.py",
    "service_composition.py",
    "structured_events.py",
}

removed_aliases = {
    "aegisops.control_plane.action_lifecycle_write_coordinator": (
        "aegisops.control_plane.actions.action_lifecycle_write_coordinator"
    ),
    "aegisops.control_plane.action_policy": (
        "aegisops.control_plane.actions.action_policy"
    ),
    "aegisops.control_plane.action_reconciliation_orchestration": (
        "aegisops.control_plane.actions.action_reconciliation_orchestration"
    ),
    "aegisops.control_plane.action_review_projection": (
        "aegisops.control_plane.actions.review.action_review_projection"
    ),
    "aegisops.control_plane.action_review_write_surface": (
        "aegisops.control_plane.actions.review.action_review_write_surface"
    ),
    "aegisops.control_plane.ai_trace_lifecycle": (
        "aegisops.control_plane.assistant.ai_trace_lifecycle"
    ),
    "aegisops.control_plane.assistant_advisory": (
        "aegisops.control_plane.assistant.assistant_advisory"
    ),
    "aegisops.control_plane.assistant_context": (
        "aegisops.control_plane.assistant.assistant_context"
    ),
    "aegisops.control_plane.case_workflow": (
        "aegisops.control_plane.ingestion.case_workflow"
    ),
    "aegisops.control_plane.detection_lifecycle": (
        "aegisops.control_plane.ingestion.detection_lifecycle"
    ),
    "aegisops.control_plane.evidence_linkage": (
        "aegisops.control_plane.ingestion.evidence_linkage"
    ),
    "aegisops.control_plane.execution_coordinator_action_requests": (
        "aegisops.control_plane.actions.execution_coordinator_action_requests"
    ),
    "aegisops.control_plane.external_evidence_boundary": (
        "aegisops.control_plane.evidence.external_evidence_boundary"
    ),
    "aegisops.control_plane.http_protected_surface": (
        "aegisops.control_plane.api.http_protected_surface"
    ),
    "aegisops.control_plane.http_runtime_surface": (
        "aegisops.control_plane.api.http_runtime_surface"
    ),
    "aegisops.control_plane.http_surface": "aegisops.control_plane.api.http_surface",
    "aegisops.control_plane.live_assistant_workflow": (
        "aegisops.control_plane.assistant.live_assistant_workflow"
    ),
    "aegisops.control_plane.pilot_reporting_export": (
        "aegisops.control_plane.reporting.pilot_reporting_export"
    ),
    "aegisops.control_plane.readiness_contracts": (
        "aegisops.control_plane.runtime.readiness_contracts"
    ),
    "aegisops.control_plane.readiness_operability": (
        "aegisops.control_plane.runtime.readiness_operability"
    ),
    "aegisops.control_plane.restore_readiness": (
        "aegisops.control_plane.runtime.restore_readiness"
    ),
    "aegisops.control_plane.restore_readiness_backup_restore": (
        "aegisops.control_plane.runtime.restore_readiness_backup_restore"
    ),
    "aegisops.control_plane.restore_readiness_projection": (
        "aegisops.control_plane.runtime.restore_readiness_projection"
    ),
    "aegisops.control_plane.runtime_boundary": (
        "aegisops.control_plane.runtime.runtime_boundary"
    ),
    "aegisops.control_plane.runtime_restore_readiness_diagnostics": (
        "aegisops.control_plane.runtime.runtime_restore_readiness_diagnostics"
    ),
}

actual_root_files = sorted(path.name for path in canonical_root.glob("*.py"))
if actual_root_files != sorted(retained_root_files):
    print(
        "Phase 52.7.5 root shim reduction expected retained canonical root files "
        + ", ".join(sorted(retained_root_files))
        + "; found "
        + ", ".join(actual_root_files),
        file=sys.stderr,
    )
    sys.exit(1)

legacy_root_files = sorted(path.name for path in legacy_root.glob("*.py"))
if legacy_root_files != ["__init__.py"]:
    print(
        "Phase 52.7.5 root shim reduction rejected legacy implementation files: "
        + ", ".join(legacy_root_files),
        file=sys.stderr,
    )
    sys.exit(1)

registry = importlib.import_module("aegisops.control_plane.core.legacy_import_aliases")
for canonical_flat, target_module in removed_aliases.items():
    legacy_flat = canonical_flat.replace(
        "aegisops.control_plane", "aegisops_control_plane", 1
    )
    legacy_target = target_module.replace(
        "aegisops.control_plane", "aegisops_control_plane", 1
    )
    if canonical_flat not in registry.CANONICAL_IMPORT_ALIASES:
        print(
            f"Phase 52.7.5 root shim reduction missing canonical alias: {canonical_flat}",
            file=sys.stderr,
        )
        sys.exit(1)
    if legacy_flat not in registry.LEGACY_IMPORT_ALIASES:
        print(
            f"Phase 52.7.5 root shim reduction missing legacy alias: {legacy_flat}",
            file=sys.stderr,
        )
        sys.exit(1)
    if importlib.import_module(canonical_flat) is not importlib.import_module(target_module):
        print(
            f"Phase 52.7.5 root shim reduction changed canonical module identity: {canonical_flat}",
            file=sys.stderr,
        )
        sys.exit(1)
    if importlib.import_module(legacy_flat) is not importlib.import_module(legacy_target):
        print(
            f"Phase 52.7.5 root shim reduction changed legacy module identity: {legacy_flat}",
            file=sys.stderr,
        )
        sys.exit(1)

print(
    "Phase 52.7.5 root shim reduction removed 25 simple canonical root shims, "
    "retained 12 explicit canonical root files, and preserved canonical plus legacy alias identity."
)
PY
