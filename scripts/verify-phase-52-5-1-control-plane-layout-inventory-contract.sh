#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md"
package_root="${repo_root}/control-plane/aegisops_control_plane"

required_headings=(
  "# ADR-0012: Phase 52.5.1 Control-Plane Layout Inventory and Migration Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Target Package Families"
  "## 4. Module Inventory"
  "## 5. Compatibility Shim Expectations"
  "## 6. Deferred Renames"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1084, #1085"
  "- **Depends On**: #1073"
  "This contract is documentation and verification only."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  "Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, adapters, DTOs, projections, summaries, and operator-facing text remain subordinate context."
  "The layout inventory does not change authorization, provenance, reconciliation, snapshot, backup, restore, export, readiness, assistant, evidence, or action-execution behavior."
  'The public Python package name `aegisops_control_plane` remains unchanged throughout Phase 52.5.1 and later child issues unless a later accepted ADR explicitly approves a rename.'
  'The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.'
  "Legacy import paths remain available during migration through compatibility shims or direct re-export modules until all documented internal, CLI, HTTP, test, and operator callers have migrated."
  "Removing a legacy import path requires a later transition policy that lists the affected import path, replacement import path, caller evidence, deprecation window, focused regression test, and rollback path."
  "If caller evidence is incomplete, malformed, or ambiguous, the old import path stays available."
  "Phase 52.5.1 does not approve production module moves, import rewrites, package renames, directory renames, Wazuh profile work, Shuffle profile work, runtime behavior changes, deployment behavior changes, or authority-boundary changes."
  'Run `bash scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`.'
  'Run `bash scripts/test-verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1085 --config <supervisor-config-path>`.'
)

allowed_families=(
  "core"
  "api"
  "runtime"
  "ingestion"
  "actions"
  "actions.review"
  "evidence"
  "assistant"
  "ml_shadow"
  "reporting"
  "adapters"
)

forbidden_claims=(
  "This contract changes runtime behavior."
  "This contract implements Wazuh product profiles."
  "This contract implements Shuffle product profiles."
  "Legacy imports may be removed immediately."
)

rendered_markdown_without_code_blocks() {
  local markdown_path="$1"

  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    in_fenced_block { next }
    substr($0, 1, 1) == "\t" { next }
    substr($0, 1, 4) == "    " { next }
    { print }
  ' "${markdown_path}" | perl -0pe 's/<!--.*?-->//gs'
}

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.5.1 control-plane layout inventory contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -d "${package_root}" ]]; then
  echo "Missing control-plane package root: ${package_root}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"
doc_raw_markdown="$(cat "${doc_path}")"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.5.1 layout contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.5.1 layout contract statement: ${phrase}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"
  local markdown="$2"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' <<<"${markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}" "${doc_raw_markdown}"; then
    echo "Forbidden Phase 52.5.1 layout contract claim: ${claim}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.5.1 layout contract: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_pattern="$(printf '%s\n' "${allowed_families[@]}" | paste -sd '|' -)"

export PHASE52_5_1_DOC_PATH="${doc_path}"
export PHASE52_5_1_PACKAGE_ROOT="${package_root}"
export PHASE52_5_1_ALLOWED_PATTERN="${allowed_pattern}"

python3 - <<'PY'
from __future__ import annotations

import os
import pathlib
import re
import sys

doc_path = pathlib.Path(os.environ["PHASE52_5_1_DOC_PATH"])
package_root = pathlib.Path(os.environ["PHASE52_5_1_PACKAGE_ROOT"])
allowed = frozenset(os.environ["PHASE52_5_1_ALLOWED_PATTERN"].split("|"))

doc_text = doc_path.read_text(encoding="utf-8")
row_pattern = re.compile(
    r"^\| `(?P<module>[^`]+\.py)` \| `(?P<family>[^`]+)` \| (?P<contract>[^|][^|]*) \|$",
    re.MULTILINE,
)

rows: dict[str, str] = {}
duplicates: set[str] = set()
invalid_families: list[str] = []
empty_contracts: list[str] = []
for match in row_pattern.finditer(doc_text):
    module = match.group("module")
    family = match.group("family").strip()
    contract = match.group("contract").strip()
    if module in rows:
        duplicates.add(module)
    rows[module] = family
    if family not in allowed:
        invalid_families.append(f"{module}: {family}")
    if not contract:
        empty_contracts.append(module)

actual_modules = sorted(
    path.relative_to(package_root).as_posix()
    for path in package_root.rglob("*.py")
    if path.is_file()
)

if duplicates:
    print(
        "Phase 52.5.1 layout inventory has duplicate module rows: "
        + ", ".join(sorted(duplicates)),
        file=sys.stderr,
    )
    sys.exit(1)

missing = [module for module in actual_modules if module not in rows]
extra = sorted(set(rows) - set(actual_modules))
if missing:
    print(
        "Phase 52.5.1 layout inventory is missing module rows: "
        + ", ".join(missing),
        file=sys.stderr,
    )
    sys.exit(1)
if extra:
    print(
        "Phase 52.5.1 layout inventory lists modules not present under control-plane/aegisops_control_plane: "
        + ", ".join(extra),
        file=sys.stderr,
    )
    sys.exit(1)
if invalid_families:
    print(
        "Phase 52.5.1 layout inventory uses unsupported target families: "
        + "; ".join(invalid_families),
        file=sys.stderr,
    )
    sys.exit(1)
if empty_contracts:
    print(
        "Phase 52.5.1 layout inventory has empty migration contract rows: "
        + ", ".join(empty_contracts),
        file=sys.stderr,
    )
    sys.exit(1)

missing_families = sorted(allowed - set(rows.values()))
if missing_families:
    print(
        "Phase 52.5.1 layout inventory does not use required target families: "
        + ", ".join(missing_families),
        file=sys.stderr,
    )
    sys.exit(1)

print(
    "Phase 52.5.1 control-plane layout inventory classifies "
    f"{len(actual_modules)} current Python files across "
    f"{len(allowed)} target package families and records migration compatibility policy."
)
PY
