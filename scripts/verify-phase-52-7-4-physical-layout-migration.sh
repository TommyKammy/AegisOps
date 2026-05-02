#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
control_plane_root="${repo_root}/control-plane"
canonical_root="${control_plane_root}/aegisops/control_plane"
legacy_root="${control_plane_root}/aegisops_control_plane"
test_path="${control_plane_root}/tests/test_phase52_7_4_physical_layout_migration.py"

for required_path in \
  "${canonical_root}/__init__.py" \
  "${canonical_root}/service.py" \
  "${canonical_root}/models.py" \
  "${canonical_root}/core/legacy_import_aliases.py" \
  "${legacy_root}/__init__.py" \
  "${test_path}"; do
  if [[ ! -f "${required_path}" ]]; then
    echo "Missing Phase 52.7.4 physical layout migration path: ${required_path#"${repo_root}/"}" >&2
    exit 1
  fi
done

if find "${legacy_root}" -mindepth 1 ! -name "__init__.py" ! -name "__pycache__" -print -quit | grep -q .; then
  echo "Phase 52.7.4 physical layout migration rejected: legacy package contains implementation files" >&2
  exit 1
fi

for removed_path in \
  "${legacy_root}/service.py" \
  "${legacy_root}/models.py" \
  "${legacy_root}/core/legacy_import_aliases.py"; do
  if [[ -e "${removed_path}" ]]; then
    echo "Phase 52.7.4 physical layout migration rejected: retained legacy implementation path ${removed_path#"${repo_root}/"}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" \
  "${legacy_root}/__init__.py" \
  "${canonical_root}/__init__.py" \
  "${canonical_root}/core/legacy_import_aliases.py" \
  "${test_path}"; then
  echo "Forbidden Phase 52.7.4 physical layout migration: workstation-local absolute path detected" >&2
  exit 1
fi

export PHASE52_7_4_CONTROL_PLANE_ROOT="${control_plane_root}"

python3 - <<'PY'
from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys

control_plane_root = Path(os.environ["PHASE52_7_4_CONTROL_PLANE_ROOT"])
if str(control_plane_root) not in sys.path:
    sys.path.insert(0, str(control_plane_root))

module_pairs = {
    "aegisops_control_plane": "aegisops.control_plane",
    "aegisops_control_plane.service": "aegisops.control_plane.service",
    "aegisops_control_plane.models": "aegisops.control_plane.models",
    "aegisops_control_plane.actions.review.action_review_chain": (
        "aegisops.control_plane.actions.review.action_review_chain"
    ),
    "aegisops_control_plane.audit_export": (
        "aegisops.control_plane.reporting.audit_export"
    ),
}

for legacy_name, canonical_name in module_pairs.items():
    try:
        legacy = importlib.import_module(legacy_name)
        canonical = importlib.import_module(canonical_name)
    except Exception as exc:
        print(
            f"Phase 52.7.4 compatibility import failed for {legacy_name}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    if legacy_name != "aegisops_control_plane" and legacy is not canonical:
        print(
            f"Phase 52.7.4 compatibility import changed module identity: {legacy_name}",
            file=sys.stderr,
        )
        sys.exit(1)

legacy_root = importlib.import_module("aegisops_control_plane")
canonical_root = importlib.import_module("aegisops.control_plane")
if legacy_root.__all__ != canonical_root.__all__:
    print("Phase 52.7.4 compatibility root changed public exports", file=sys.stderr)
    sys.exit(1)

for attribute in (
    "AegisOpsControlPlaneService",
    "AlertRecord",
    "RuntimeConfig",
    "build_runtime_service",
):
    if getattr(legacy_root, attribute, None) is not getattr(canonical_root, attribute, None):
        print(
            f"Phase 52.7.4 compatibility root changed public attribute identity: {attribute}",
            file=sys.stderr,
        )
        sys.exit(1)

print("Phase 52.7.4 physical layout migration verifier passed.")
PY
