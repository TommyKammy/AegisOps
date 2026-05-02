#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0015-phase-52-6-3-legacy-import-alias-registry.md"
registry_path="${repo_root}/control-plane/aegisops_control_plane/core/legacy_import_aliases.py"
control_plane_root="${repo_root}/control-plane"
removed_root_shim="${repo_root}/control-plane/aegisops_control_plane/audit_export.py"

required_phrases=(
  "# ADR-0015: Phase 52.6.3 Legacy Import Alias Registry"
  "- **Status**: Accepted"
  "- **Date**: 2026-05-02"
  "- **Related Issues**: #1105, #1108"
  "- **Depends On**: #1107"
  "The registry lives at \`control-plane/aegisops_control_plane/core/legacy_import_aliases.py\`."
  "| \`aegisops_control_plane.audit_export\` | \`aegisops_control_plane.reporting.audit_export\` | \`reporting\` | \`reporting/audit_export.py\` |"
  "The \`audit_export.py\` root shim is the only Phase 52.6.3 physical deletion."
  "Alias rows without an explicit target owner fail verification."
  "An approved legacy import path disappearing without an alias row or retained physical shim fails verification."
  "Run \`bash scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh\`."
  "Run \`bash scripts/test-verify-phase-52-6-3-legacy-import-alias-registry.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1108 --config <supervisor-config-path>\`."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.6.3 legacy import alias registry ADR: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${registry_path}" ]]; then
  echo "Missing Phase 52.6.3 legacy import alias registry: ${registry_path}" >&2
  exit 1
fi

if [[ -e "${removed_root_shim}" ]]; then
  echo "Phase 52.6.3 proof-of-pattern root shim should be removed: control-plane/aegisops_control_plane/audit_export.py" >&2
  exit 1
fi

doc_text="$(cat "${doc_path}")"
for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_text}"; then
    echo "Missing Phase 52.6.3 legacy import alias registry statement: ${phrase}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}" "${registry_path}"; then
  echo "Forbidden Phase 52.6.3 legacy import alias registry: workstation-local absolute path detected" >&2
  exit 1
fi

export PHASE52_6_3_CONTROL_PLANE_ROOT="${control_plane_root}"

python3 - <<'PY'
from __future__ import annotations

import importlib
import os
import pathlib
import sys

control_plane_root = pathlib.Path(os.environ["PHASE52_6_3_CONTROL_PLANE_ROOT"])
if str(control_plane_root) not in sys.path:
    sys.path.insert(0, str(control_plane_root))

try:
    registry = importlib.import_module(
        "aegisops_control_plane.core.legacy_import_aliases"
    )
except Exception as exc:
    print(
        f"Phase 52.6.3 legacy import alias registry failed to load: {exc}",
        file=sys.stderr,
    )
    sys.exit(1)

required_aliases = {
    "aegisops_control_plane.audit_export": (
        "aegisops_control_plane.reporting.audit_export",
        "reporting",
        "reporting/audit_export.py",
        "export_audit_retention_baseline",
    ),
}
required_blockers = {
    "aegisops_control_plane.service",
    "aegisops_control_plane.models",
    "aegisops_control_plane.phase29_shadow_dataset",
    "aegisops_control_plane.phase29_shadow_scoring",
    "aegisops_control_plane.phase29_evidently_drift_visibility",
    "aegisops_control_plane.phase29_mlflow_shadow_model_registry",
}

aliases = registry.LEGACY_IMPORT_ALIASES
for legacy_path, (target_path, target_family, owner, attribute) in required_aliases.items():
    alias = aliases.get(legacy_path)
    if alias is None:
        print(
            f"Phase 52.6.3 legacy import alias registry missing approved alias: {legacy_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    if alias.target_module != target_path:
        print(
            f"Phase 52.6.3 legacy import alias target mismatch for {legacy_path}: {alias.target_module}",
            file=sys.stderr,
        )
        sys.exit(1)
    if alias.target_family != target_family or alias.owner != owner:
        print(
            f"Phase 52.6.3 legacy import alias missing target owner metadata for {legacy_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    legacy_module = importlib.import_module(legacy_path)
    target_module = importlib.import_module(target_path)
    if legacy_module is not target_module:
        print(
            f"Phase 52.6.3 legacy import alias changed module identity for {legacy_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    if getattr(legacy_module, attribute) is not getattr(target_module, attribute):
        print(
            f"Phase 52.6.3 legacy import alias changed implementation behavior for {legacy_path}:{attribute}",
            file=sys.stderr,
        )
        sys.exit(1)

blockers = registry.RETAINED_COMPATIBILITY_BLOCKERS
missing_blockers = sorted(required_blockers - set(blockers))
if missing_blockers:
    print(
        "Phase 52.6.3 legacy import alias registry is missing retained blockers: "
        + ", ".join(missing_blockers),
        file=sys.stderr,
    )
    sys.exit(1)

print(
    "Phase 52.6.3 legacy import alias registry preserves approved aliases, "
    "keeps target owner metadata explicit, and lists retained blockers."
)
PY
