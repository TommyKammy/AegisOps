#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
inventory_doc="${repo_root}/docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md"
package_root="${repo_root}/control-plane/aegisops_control_plane"

approved_scaffold_roots=(
  "core"
  "api"
  "runtime"
  "ingestion"
  "actions"
  "evidence"
  "assistant"
  "ml_shadow"
  "reporting"
)

if [[ ! -f "${inventory_doc}" ]]; then
  echo "Missing Phase 52.5.1 layout inventory for guardrail: ${inventory_doc}" >&2
  exit 1
fi

if [[ ! -d "${package_root}" ]]; then
  echo "Missing control-plane package root for guardrail: ${package_root}" >&2
  exit 1
fi

export PHASE52_5_2_INVENTORY_DOC="${inventory_doc}"
export PHASE52_5_2_PACKAGE_ROOT="${package_root}"
export PHASE52_5_2_SCAFFOLD_ROOTS="$(printf '%s\n' "${approved_scaffold_roots[@]}")"

python3 - <<'PY'
from __future__ import annotations

import os
import pathlib
import re
import sys

inventory_doc = pathlib.Path(os.environ["PHASE52_5_2_INVENTORY_DOC"])
package_root = pathlib.Path(os.environ["PHASE52_5_2_PACKAGE_ROOT"])
approved_scaffold_roots = {
    line
    for line in os.environ["PHASE52_5_2_SCAFFOLD_ROOTS"].splitlines()
    if line.strip()
}

doc_text = inventory_doc.read_text(encoding="utf-8")
row_pattern = re.compile(
    r"^\| `(?P<module>[^`]+\.py)` \| `(?P<family>[^`]+)` \| (?P<contract>[^|][^|]*) \|$",
    re.MULTILINE,
)
classified_module_contracts = {
    match.group("module"): match.group("contract").strip()
    for match in row_pattern.finditer(doc_text)
}
classified_modules = set(classified_module_contracts)

unclassified_flat_modules: list[str] = []
for path in package_root.glob("*.py"):
    relative = path.relative_to(package_root).as_posix()
    if relative not in classified_modules:
        unclassified_flat_modules.append(relative)

missing_scaffold_markers = []
phase_numbered_production_modules = []
phase_numbered_name_pattern = re.compile(r"^phase\d+_.*\.py$")
for path in package_root.rglob("*.py"):
    relative = path.relative_to(package_root).as_posix()
    if not phase_numbered_name_pattern.match(path.name):
        continue
    contract = classified_module_contracts.get(relative)
    if contract is None or not contract.startswith("Compatibility shim only"):
        phase_numbered_production_modules.append(relative)

for scaffold_root in approved_scaffold_roots:
    init_relative = f"{scaffold_root}/__init__.py"
    init_path = package_root / init_relative
    if not init_path.is_file():
        missing_scaffold_markers.append(init_relative)
    elif init_relative not in classified_modules:
        missing_scaffold_markers.append(f"{init_relative} (not classified)")

review_marker = package_root / "actions" / "review" / "__init__.py"
if not review_marker.is_file():
    missing_scaffold_markers.append("actions/review/__init__.py")
elif "actions/review/__init__.py" not in classified_modules:
    missing_scaffold_markers.append("actions/review/__init__.py (not classified)")

if unclassified_flat_modules:
    print(
        "Phase 52.5.2 layout guardrail found unclassified flat root-level modules: "
        + ", ".join(sorted(unclassified_flat_modules)),
        file=sys.stderr,
    )
    sys.exit(1)

if missing_scaffold_markers:
    print(
        "Phase 52.5.2 layout guardrail found unclassified package scaffolds: "
        + ", ".join(sorted(missing_scaffold_markers)),
        file=sys.stderr,
    )
    sys.exit(1)

if phase_numbered_production_modules:
    print(
        "Phase 52.5.2 layout guardrail found phase-numbered production modules "
        "without compatibility-shim classification: "
        + ", ".join(sorted(phase_numbered_production_modules)),
        file=sys.stderr,
    )
    sys.exit(1)

print(
    "Phase 52.5.2 layout guardrail accepts the current classified baseline and rejects new unclassified or phase-numbered production modules."
)
PY
