#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
control_plane_root="${repo_root}/control-plane"
bridge_root="${control_plane_root}/aegisops"
bridge_package="${bridge_root}/control_plane"
doc_path="${repo_root}/docs/adr/0017-phase-52-7-2-canonical-namespace-bridge.md"

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.7.2 canonical namespace bridge ADR: docs/adr/0017-phase-52-7-2-canonical-namespace-bridge.md" >&2
  exit 1
fi

for required_path in \
  "${bridge_root}/__init__.py" \
  "${bridge_package}/__init__.py" \
  "${control_plane_root}/aegisops_control_plane/__init__.py"; do
  if [[ ! -f "${required_path}" ]]; then
    echo "Missing Phase 52.7.2 canonical namespace bridge path: ${required_path#${repo_root}/}" >&2
    exit 1
  fi
done

mac_home_segment="Users"
linux_home_segment="home"
windows_home_segment="Users"
workstation_path_pattern="(/${mac_home_segment}/[^[:space:]]+|/${linux_home_segment}/[^[:space:]]+|[A-Za-z]:\\\\${windows_home_segment}\\\\)"

if grep -R -E "${workstation_path_pattern}" \
  "${doc_path}" \
  "${bridge_root}" \
  "${repo_root}/control-plane/tests/test_phase52_7_2_canonical_namespace_bridge.py" >/dev/null; then
  echo "Forbidden Phase 52.7.2 canonical namespace bridge: workstation-local absolute path detected" >&2
  exit 1
fi

export PHASE52_7_2_CONTROL_PLANE_ROOT="${control_plane_root}"

python3 - <<'PY'
from __future__ import annotations

import importlib
import os
import pathlib
import sys

control_plane_root = pathlib.Path(os.environ["PHASE52_7_2_CONTROL_PLANE_ROOT"])
if str(control_plane_root) not in sys.path:
    sys.path.insert(0, str(control_plane_root))

try:
    legacy = importlib.import_module("aegisops_control_plane")
    canonical = importlib.import_module("aegisops.control_plane")
except Exception as exc:
    print(f"Phase 52.7.2 canonical namespace bridge failed to load: {exc}", file=sys.stderr)
    sys.exit(1)

for attribute in (
    "AegisOpsControlPlaneService",
    "AlertRecord",
    "RuntimeConfig",
    "build_runtime_service",
):
    if getattr(canonical, attribute, None) is not getattr(legacy, attribute, None):
        print(
            f"Phase 52.7.2 canonical namespace bridge changed public attribute identity: {attribute}",
            file=sys.stderr,
        )
        sys.exit(1)

module_pairs = {
    "aegisops.control_plane.service": "aegisops_control_plane.service",
    "aegisops.control_plane.models": "aegisops_control_plane.models",
    "aegisops.control_plane.actions.review.action_review_chain": (
        "aegisops_control_plane.actions.review.action_review_chain"
    ),
    "aegisops.control_plane.reporting.audit_export": "aegisops_control_plane.reporting.audit_export",
}

for canonical_name, legacy_name in module_pairs.items():
    canonical_module = importlib.import_module(canonical_name)
    legacy_module = importlib.import_module(legacy_name)
    if canonical_module is not legacy_module:
        print(
            f"Phase 52.7.2 canonical namespace bridge changed module identity: {canonical_name}",
            file=sys.stderr,
        )
        sys.exit(1)

importlib.import_module("aegisops_control_plane")
importlib.import_module("aegisops_control_plane.service")

print("Phase 52.7.2 canonical namespace bridge verifier passed.")
PY
