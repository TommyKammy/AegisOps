#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0016-phase-52-7-1-namespace-and-layout-inventory-contract.md"
package_root="${repo_root}/control-plane/aegisops_control_plane"
proposed_package_root="${repo_root}/control-plane/aegisops/control_plane"

required_headings=(
  "# ADR-0016: Phase 52.7.1 Namespace and Layout Inventory Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Inventory Scope"
  "## 4. Namespace And Layout Inventory"
  "## 5. Compatibility And Blockers"
  "## 6. Movement Guard"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-02"
  "- **Related Issues**: #1120, #1121"
  "- **Depends On**: #1112"
  "This contract is documentation and verification only. It does not move files, rewrite imports, delete shims, change packaging, alter CI behavior, change supervisor policy, start Wazuh profile work, start Shuffle profile work, or alter runtime behavior."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  "Namespace bridges, filesystem layout, compatibility aliases, generated config, docs, verifier output, CI status, supervisor-facing issue text, UI cache, browser state, downstream receipts, Wazuh, Shuffle, tickets, assistant output, optional evidence, and demo data remain subordinate evidence or implementation context."
  "Every row below is a migration prerequisite, not migration approval. If caller evidence is missing, malformed, ambiguous, or only partially trusted, the current reference remains the supported reference and the proposed reference remains blocked."
  'The public Python package name `aegisops_control_plane` remains unchanged in Phase 52.7.1.'
  'The proposed canonical namespace `aegisops.control_plane` is a future target only. It is not implemented, imported, packaged, or advertised as available by this slice.'
  'The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.'
  '`service.py` remains a retained compatibility blocker under ADR-0003, ADR-0010, ADR-0014, and the Phase 52.6 closeout evaluation.'
  'Phase 52.7.1 rejects file movement. The current `control-plane/aegisops_control_plane/` package, `control-plane/main.py`, `.github/workflows/ci.yml`, this ADR, and the focused verifier scripts must remain at the inventory paths above.'
  "The current package file manifest remains governed by ADR-0012 and the retained-root owner policy remains governed by ADR-0014. This ADR adds the namespace/layout row contract above those existing inventories; it does not replace them."
  'Run `bash scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh`.'
  'Run `bash scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `bash scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`.'
  'Run `bash scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1120 --config <supervisor-config-path>`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1121 --config <supervisor-config-path>`.'
)

required_rows=(
  'current filesystem path|control-plane/aegisops_control_plane/|control-plane/aegisops/control_plane/'
  'current import package|aegisops_control_plane|aegisops.control_plane'
  'proposed canonical namespace|aegisops_control_plane|aegisops.control_plane'
  'packaging entrypoint|python3 control-plane/main.py|python3 control-plane/main.py'
  'docs path|docs/adr/0016-phase-52-7-1-namespace-and-layout-inventory-contract.md|docs/adr/0016-phase-52-7-1-namespace-and-layout-inventory-contract.md'
  'script path|scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh|scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh'
  'negative fixture test path|scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh|scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh'
  'CI path|.github/workflows/ci.yml|.github/workflows/ci.yml'
  'supervisor-facing path|node <codex-supervisor-root>/dist/index.js issue-lint 1121 --config <supervisor-config-path>|node <codex-supervisor-root>/dist/index.js issue-lint 1121 --config <supervisor-config-path>'
)

forbidden_claims=(
  "This contract changes runtime behavior."
  "The \`aegisops.control_plane\` namespace is importable now."
  "The \`aegisops_control_plane\` package may be removed immediately."
  "This contract implements Wazuh product profiles."
  "This contract implements Shuffle product profiles."
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
  echo "Missing Phase 52.7.1 namespace/layout inventory contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -d "${package_root}" ]]; then
  echo "Phase 52.7.1 file movement rejected: missing current package path control-plane/aegisops_control_plane/" >&2
  exit 1
fi

if [[ -d "${proposed_package_root}" ]]; then
  echo "Phase 52.7.1 namespace/layout inventory rejected: proposed package path already exists at control-plane/aegisops/control_plane/" >&2
  exit 1
fi

for required_path in \
  "${repo_root}/control-plane/main.py" \
  "${repo_root}/.github/workflows/ci.yml" \
  "${repo_root}/scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh" \
  "${repo_root}/scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh"
do
  if [[ ! -f "${required_path}" ]]; then
    required_path_display="${required_path#"${repo_root}/"}"
    echo "Phase 52.7.1 file movement rejected: missing current path ${required_path_display}" >&2
    exit 1
  fi
done

doc_rendered_markdown="$(rendered_markdown_without_code_blocks "${doc_path}")"
doc_raw_markdown="$(cat "${doc_path}")"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.7.1 namespace/layout heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.7.1 namespace/layout statement: ${phrase}" >&2
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
    echo "Forbidden Phase 52.7.1 namespace/layout claim: ${claim}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.7.1 namespace/layout inventory: workstation-local absolute path detected" >&2
  exit 1
fi

export PHASE52_7_1_DOC_PATH="${doc_path}"
export PHASE52_7_1_REQUIRED_ROWS="$(printf '%s\n' "${required_rows[@]}")"

python3 - <<'PY'
from __future__ import annotations

import os
import pathlib
import re
import sys

doc_path = pathlib.Path(os.environ["PHASE52_7_1_DOC_PATH"])
required_rows = [line.split("|", 2) for line in os.environ["PHASE52_7_1_REQUIRED_ROWS"].splitlines()]
doc_text = doc_path.read_text(encoding="utf-8")

row_pattern = re.compile(
    r"^\| `(?P<class>[^`]+)` \| `(?P<current>[^`]+)` \| `(?P<proposed>[^`]+)` \| (?P<contract>[^|][^|]*) \|$",
    re.MULTILINE,
)

rows: dict[str, tuple[str, str, str]] = {}
duplicates: set[str] = set()
empty_contracts: list[str] = []
for match in row_pattern.finditer(doc_text):
    row_class = match.group("class")
    if row_class in rows:
        duplicates.add(row_class)
    rows[row_class] = (
        match.group("current"),
        match.group("proposed"),
        match.group("contract").strip(),
    )
    if not match.group("contract").strip():
        empty_contracts.append(row_class)

if duplicates:
    print(
        "Phase 52.7.1 namespace/layout inventory has duplicate rows: "
        + ", ".join(sorted(duplicates)),
        file=sys.stderr,
    )
    sys.exit(1)

for row_class, current, proposed in required_rows:
    if row_class not in rows:
        print(f"Missing Phase 52.7.1 namespace inventory row: {row_class}", file=sys.stderr)
        sys.exit(1)
    actual_current, actual_proposed, _ = rows[row_class]
    if actual_current != current:
        print(
            f"Phase 52.7.1 namespace inventory current reference mismatch for {row_class}: "
            f"expected {current}, got {actual_current}",
            file=sys.stderr,
        )
        sys.exit(1)
    if actual_proposed != proposed:
        print(
            f"Phase 52.7.1 namespace inventory proposed reference mismatch for {row_class}: "
            f"expected {proposed}, got {actual_proposed}",
            file=sys.stderr,
        )
        sys.exit(1)

if empty_contracts:
    print(
        "Phase 52.7.1 namespace/layout inventory has empty contract rows: "
        + ", ".join(empty_contracts),
        file=sys.stderr,
    )
    sys.exit(1)

if "aegisops_control_plane" not in doc_text:
    print("Missing current aegisops_control_plane references in Phase 52.7.1 namespace inventory.", file=sys.stderr)
    sys.exit(1)
if "aegisops.control_plane" not in doc_text:
    print("Missing proposed canonical namespace references in Phase 52.7.1 namespace inventory.", file=sys.stderr)
    sys.exit(1)

print(
    "Phase 52.7.1 namespace/layout inventory records current package, proposed namespace, "
    "entrypoint, docs, script, CI, and supervisor-facing references."
)
PY

for prerequisite in \
  "${repo_root}/scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh" \
  "${repo_root}/scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh"
do
  if [[ ! -f "${prerequisite}" ]]; then
    echo "Missing prerequisite verifier: $(basename "${prerequisite}")" >&2
    exit 1
  fi
  bash "${prerequisite}" "${repo_root}" >/dev/null
done
