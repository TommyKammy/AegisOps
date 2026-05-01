#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md"
control_plane_root="${repo_root}/control-plane"

required_imports=(
  "aegisops_control_plane.service:AegisOpsControlPlaneService"
  "aegisops_control_plane.models:AlertRecord"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.5.2 compatibility-shim policy: ${doc_path}" >&2
  exit 1
fi

for import_spec in "${required_imports[@]}"; do
  if ! grep -Fq -- "${import_spec}" "${doc_path}"; then
    echo "Missing Phase 52.5.2 documented legacy import compatibility check: ${import_spec}" >&2
    exit 1
  fi
done

export PHASE52_5_2_CONTROL_PLANE_ROOT="${control_plane_root}"
export PHASE52_5_2_REQUIRED_IMPORTS="$(printf '%s\n' "${required_imports[@]}")"

python3 - <<'PY'
from __future__ import annotations

import importlib
import os
import pathlib
import sys

control_plane_root = pathlib.Path(os.environ["PHASE52_5_2_CONTROL_PLANE_ROOT"])
if str(control_plane_root) not in sys.path:
    sys.path.insert(0, str(control_plane_root))

required_imports = [
    line
    for line in os.environ["PHASE52_5_2_REQUIRED_IMPORTS"].splitlines()
    if line.strip()
]

for import_spec in required_imports:
    module_name, attribute_name = import_spec.split(":", 1)
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - shell verifier reports detail.
        print(
            f"Phase 52.5.2 legacy import failed: {module_name}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    if not hasattr(module, attribute_name):
        print(
            f"Phase 52.5.2 legacy import missing attribute: {import_spec}",
            file=sys.stderr,
        )
        sys.exit(1)

print(
    "Phase 52.5.2 import compatibility verifier preserved stable legacy imports: "
    + ", ".join(required_imports)
)
PY
