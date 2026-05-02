#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md"
package_root="${repo_root}/control-plane/aegisops_control_plane"

required_phrases=(
  'After Phase 52.6.6, the only retained root owner files are'
  '`__init__.py`, `config.py`, `models.py`, `operator_inspection.py`, `persistence_lifecycle.py`, `publishable_paths.py`, `record_validation.py`, `reviewed_slice_policy.py`, `service_composition.py`, and `structured_events.py`.'
  '`service.py` is not a retained owner; it is the single retained compatibility blocker'
  'No other direct root Python file may be promoted to retained owner status without a later accepted ADR or issue-specific contract that names the root file, authoritative owner, caller evidence, focused regression coverage, rollback path, and authority-boundary impact.'
  'The root package guardrail baseline is exactly `37` direct `.py` files under `control-plane/aegisops_control_plane/`.'
  'No direct root Python filename may begin with `phaseNN` or `phaseNN_` after Phase 52.6.6.'
  'A new flat root module fails verification unless the root file inventory classifies it and the root-count baseline is intentionally updated by policy.'
  'The future public package rename, outer `control-plane/` directory rename, retained-root owner relocation, and `service.py` facade relocation remain blocked until a later accepted ADR names caller evidence, replacement paths, deprecation window, focused regression coverage, rollback path, and authority-boundary impact.'
  'Run `bash scripts/verify-phase-52-6-6-root-package-guardrails.sh`.'
  'Run `bash scripts/test-verify-phase-52-6-6-root-package-guardrails.sh`.'
  'Run `bash scripts/verify-phase-52-5-2-layout-guardrail.sh`.'
  'Run `bash scripts/verify-phase-52-5-9-service-facade-freeze.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1111 --config <supervisor-config-path>`.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.6 root shim inventory contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -d "${package_root}" ]]; then
  echo "Missing control-plane package root: control-plane/aegisops_control_plane" >&2
  exit 1
fi

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    if [[ "${phrase}" == "The future public package rename,"* ]]; then
      echo "Missing Phase 52.6.6 future blocker statement: ${phrase}" >&2
      exit 1
    fi
    echo "Missing Phase 52.6.6 retained root owner policy statement: ${phrase}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.6.6 root package guardrail artifact: workstation-local absolute path detected" >&2
  exit 1
fi

export PHASE52_6_6_DOC_PATH="${doc_path}"
export PHASE52_6_6_PACKAGE_ROOT="${package_root}"

python3 - <<'PY'
from __future__ import annotations

import os
from pathlib import Path
import re
import sys

doc_path = Path(os.environ["PHASE52_6_6_DOC_PATH"])
package_root = Path(os.environ["PHASE52_6_6_PACKAGE_ROOT"])

expected_root_count = 37
expected_retained_owners = {
    "__init__.py",
    "config.py",
    "models.py",
    "operator_inspection.py",
    "persistence_lifecycle.py",
    "publishable_paths.py",
    "record_validation.py",
    "reviewed_slice_policy.py",
    "service_composition.py",
    "structured_events.py",
}
allowed_classifications = {
    "retained owner",
    "simple shim",
    "compatibility adapter",
    "alias candidate",
    "retained compatibility blocker",
}
phase_numbered_pattern = re.compile(r"^phase\d+")
row_pattern = re.compile(
    r"^\| `(?P<module>[^`]+\.py)` \| `(?P<family>[^`]+)` \| "
    r"(?P<classification>[^|]+) \| (?P<decision>[^|][^|]*) \|$",
    re.MULTILINE,
)

actual_root_files = sorted(path.name for path in package_root.glob("*.py") if path.is_file())
phase_numbered = [name for name in actual_root_files if phase_numbered_pattern.match(name)]
if phase_numbered:
    print(
        "Phase 52.6.6 root package guardrail rejects phase-numbered root filenames: "
        + ", ".join(phase_numbered),
        file=sys.stderr,
    )
    sys.exit(1)

if len(actual_root_files) != expected_root_count:
    print(
        "Phase 52.6.6 root package guardrail expected "
        f"{expected_root_count} direct root Python files, found {len(actual_root_files)}.",
        file=sys.stderr,
    )
    sys.exit(1)

doc_text = doc_path.read_text(encoding="utf-8")
rows: dict[str, str] = {}
duplicates: set[str] = set()
invalid_classifications: list[str] = []
for match in row_pattern.finditer(doc_text):
    module = match.group("module")
    if module in rows:
        duplicates.add(module)
    classification = match.group("classification").strip()
    if classification not in allowed_classifications:
        invalid_classifications.append(f"{module}: {classification}")
    rows[module] = classification

if duplicates:
    print(
        "Phase 52.6.6 root package guardrail found duplicate root inventory rows: "
        + ", ".join(sorted(duplicates)),
        file=sys.stderr,
    )
    sys.exit(1)

if invalid_classifications:
    print(
        "Phase 52.6.6 root package guardrail found invalid root inventory "
        "classifications: "
        + ", ".join(sorted(invalid_classifications)),
        file=sys.stderr,
    )
    sys.exit(1)

missing_rows = [name for name in actual_root_files if name not in rows]
extra_rows = sorted(set(rows) - set(actual_root_files))
if missing_rows:
    print(
        "Phase 52.6.6 root package guardrail found unclassified flat root modules: "
        + ", ".join(missing_rows),
        file=sys.stderr,
    )
    sys.exit(1)
if extra_rows:
    print(
        "Phase 52.6.6 root package guardrail inventory lists absent root files: "
        + ", ".join(extra_rows),
        file=sys.stderr,
    )
    sys.exit(1)

actual_retained_owners = {
    module for module, classification in rows.items() if classification == "retained owner"
}
missing_retained_owners = sorted(expected_retained_owners - actual_retained_owners)
unexpected_retained_owners = sorted(actual_retained_owners - expected_retained_owners)
if missing_retained_owners or unexpected_retained_owners:
    parts: list[str] = []
    if missing_retained_owners:
        parts.append("missing retained owner rows: " + ", ".join(missing_retained_owners))
    if unexpected_retained_owners:
        parts.append("unexpected retained owner rows: " + ", ".join(unexpected_retained_owners))
    print(
        "Phase 52.6.6 retained root owner set mismatch: " + "; ".join(parts),
        file=sys.stderr,
    )
    sys.exit(1)

if rows.get("service.py") != "retained compatibility blocker":
    print(
        "Phase 52.6.6 root package guardrail requires service.py to remain "
        "a retained compatibility blocker, not a retained owner.",
        file=sys.stderr,
    )
    sys.exit(1)

print(
    "Phase 52.6.6 root package guardrails retain 37 root Python files, "
    "pin the retained-owner set, reject phase-numbered root filenames, "
    "and keep service.py under retained compatibility-blocker policy."
)
PY
