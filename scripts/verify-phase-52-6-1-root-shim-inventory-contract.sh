#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md"
package_root="${repo_root}/control-plane/aegisops/control_plane"

required_headings=(
  "# ADR-0014: Phase 52.6.1 Root Shim Inventory and Deprecation Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Phase 52.5 Root File Baseline"
  "## 4. Classification Rules"
  "## 5. Root File Inventory"
  "## 6. Phase29 Boundary"
  "## 7. Deprecation Decision Rules"
  "## 8. Forbidden Claims"
  "## 9. Validation"
  "## 10. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-02"
  "- **Related Issues**: #1105, #1106, #1110"
  "- **Depends On**: #1094"
  "This contract is documentation and verification only. Phase 52.6.3 removes only \`audit_export.py\` as the proof-of-pattern alias-registry candidate; it does not delete broad shim sets, rename the public package, change the outer \`control-plane/\` directory, start Wazuh profile work, start Shuffle profile work, or alter runtime behavior."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  "Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, adapters, DTOs, projections, summaries, compatibility shims, alias rows, and operator-facing text remain subordinate context."
  "The root shim inventory does not change authorization, provenance, reconciliation, snapshot, backup, restore, export, readiness, assistant, evidence, action-execution, Wazuh, Shuffle, ticket, CLI, HTTP, or deployment behavior."
  "The Phase 52.6.5 root-level Python file count under \`control-plane/aegisops_control_plane/\` is \`37\` after removing simple physical root shims and the Phase29 root filenames covered by the legacy import alias registry and focused compatibility tests."
  "The baseline counts only direct \`.py\` files in \`control-plane/aegisops_control_plane/\`; package-owned files below subdirectories are tracked by ADR-0012 and stay outside this root shim baseline."
  "The retired Phase29 root filenames were legacy compatibility adapters only. They were not production owners."
  "The domain-owned implementations are the directly linked \`ml_shadow\` modules listed in the retired filename list. Legacy \`phase29_*\` import paths remain available only through the alias registry and focused compatibility tests."
  "Physical root shim deletion is allowed only when a later issue records the exact root file, replacement owner import path, caller evidence, deprecation window, focused legacy-import regression, rollback path, and authority-boundary impact."
  "Alias preservation is allowed only when the alias remains a narrow reference to the moved owner and does not make compatibility state, summary text, or module identity authoritative workflow truth."
  "Retained blockers stay physically present until the referenced compatibility policy is superseded by a later accepted ADR or issue-specific contract."
  "If a prerequisite signal is missing, malformed, ambiguous, or only partially trusted, the deletion path fails closed and the root file stays available."
  "Run \`bash scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-52-6-1-root-shim-inventory-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`bash scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh\`."
  "Run \`bash scripts/test-verify-phase-52-6-3-legacy-import-alias-registry.sh\`."
  "Run \`bash scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh\`."
  "Run \`bash scripts/test-verify-phase-52-6-5-retire-phase29-root-filenames.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1110 --config <supervisor-config-path>\`."
)

allowed_classifications=(
  "retained owner"
  "simple shim"
  "compatibility adapter"
  "alias candidate"
  "retained compatibility blocker"
)

forbidden_claims=(
  "This contract changes runtime behavior."
  "This contract allows Phase29 root files as production owners."
  "Legacy root shims may be deleted immediately."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.6.1 root shim inventory contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -d "${package_root}" ]]; then
  echo "Missing control-plane package root: ${package_root}" >&2
  exit 1
fi

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

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"
doc_raw_markdown="$(cat "${doc_path}")"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.6.1 root shim inventory heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.6.1 root shim inventory statement: ${phrase}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"
  local markdown="$2"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 8\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' <<<"${markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}" "${doc_raw_markdown}"; then
    echo "Forbidden Phase 52.6.1 root shim inventory claim: ${claim}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.6.1 root shim inventory: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_pattern="$(printf '%s\n' "${allowed_classifications[@]}" | paste -sd '|' -)"

export PHASE52_6_1_DOC_PATH="${doc_path}"
export PHASE52_6_1_PACKAGE_ROOT="${package_root}"
export PHASE52_6_1_ALLOWED_PATTERN="${allowed_pattern}"

python3 - <<'PY'
from __future__ import annotations

import os
import pathlib
import re
import sys

doc_path = pathlib.Path(os.environ["PHASE52_6_1_DOC_PATH"])
package_root = pathlib.Path(os.environ["PHASE52_6_1_PACKAGE_ROOT"])
allowed = frozenset(os.environ["PHASE52_6_1_ALLOWED_PATTERN"].split("|"))

doc_text = doc_path.read_text(encoding="utf-8")
row_pattern = re.compile(
    r"^\| `(?P<module>[^`]+\.py)` \| `(?P<family>[^`]+)` \| (?P<classification>[^|]+) \| (?P<decision>[^|][^|]*) \|$",
    re.MULTILINE,
)

rows: dict[str, tuple[str, str]] = {}
duplicates: set[str] = set()
invalid_classifications: list[str] = []
empty_decisions: list[str] = []
for match in row_pattern.finditer(doc_text):
    module = match.group("module")
    classification = match.group("classification").strip()
    decision = match.group("decision").strip()
    if module in rows:
        duplicates.add(module)
    rows[module] = (classification, decision)
    if classification not in allowed:
        invalid_classifications.append(f"{module}: {classification}")
    if not decision:
        empty_decisions.append(module)

actual_modules = sorted(
    path.name
    for path in package_root.glob("*.py")
    if path.is_file()
)

if duplicates:
    print(
        "Phase 52.6.1 root shim inventory has duplicate root file rows: "
        + ", ".join(sorted(duplicates)),
        file=sys.stderr,
    )
    sys.exit(1)

missing = [module for module in actual_modules if module not in rows]
if missing:
    print(
        "Phase 52.6.1 root shim inventory is missing root file rows: "
        + ", ".join(missing),
        file=sys.stderr,
    )
    sys.exit(1)
if len(actual_modules) != 12:
    print(
        f"Phase 52.6.1 root shim inventory expected Phase 52.7.5 canonical root count of 12 files, found {len(actual_modules)}.",
        file=sys.stderr,
    )
    sys.exit(1)
if invalid_classifications:
    print(
        "Phase 52.6.1 root shim inventory uses unsupported classifications: "
        + "; ".join(invalid_classifications),
        file=sys.stderr,
    )
    sys.exit(1)
if empty_decisions:
    print(
        "Phase 52.6.1 root shim inventory has empty deprecation decision rows: "
        + ", ".join(empty_decisions),
        file=sys.stderr,
    )
    sys.exit(1)

required_classifications = {
    "retained owner",
    "retained compatibility blocker",
}
missing_classifications = sorted(required_classifications - {row[0] for row in rows.values()})
if missing_classifications:
    print(
        "Phase 52.6.1 root shim inventory does not use required classifications: "
        + ", ".join(missing_classifications),
        file=sys.stderr,
    )
    sys.exit(1)

phase29_modules = sorted(module for module in actual_modules if module.startswith("phase29_"))
if phase29_modules:
    print(
        "Phase 52.6.1 root shim inventory must not retain Phase29 root filenames after Phase 52.6.5: "
        + ", ".join(phase29_modules),
        file=sys.stderr,
    )
    sys.exit(1)

if rows.get("service.py", ("", ""))[0] != "retained compatibility blocker":
    print(
        "Phase 52.6.1 root shim inventory must classify service.py as a retained compatibility blocker.",
        file=sys.stderr,
    )
    sys.exit(1)

print(
    "Phase 52.6.1 root shim inventory classifies "
    f"{len(actual_modules)} root Python files, records the Phase 52.5 baseline, "
    "keeps Phase29 root filenames retired, and documents deprecation rules."
)
PY
