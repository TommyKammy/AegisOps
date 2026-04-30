#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0010-phase-50-13-public-facade-api-inventory-and-compatibility-policy.md"
service_path="${repo_root}/control-plane/aegisops_control_plane/service.py"

required_headings=(
  "# ADR-0010: Phase 50.13 Public Facade API Inventory and Compatibility Policy"
  "## 1. Context"
  "## 2. Decision"
  "## 3. Starting Measurements"
  "## 4. Public Facade Inventory"
  "## 5. Compatibility Delegate Policy"
  "## 6. Validation"
  "## 7. Non-Goals"
  "## 8. Approval"
)

required_phrases=(
  '- **Status**: Accepted'
  '- **Date**: 2026-04-30'
  '- **Related Issues**: #1030, #1031'
  '- **Depends On**: #1022'
  'ADR-0003 remains authoritative for the public facade-preservation exception.'
  'ADR-0004 through ADR-0009 remain authoritative unless a later accepted ADR explicitly supersedes a narrower maintainability decision.'
  'Phase 50.12.7 records the accepted residual `service.py` closeout state before Phase 50.13 starts.'
  'This ADR does not remove, move, rename, or change any public `AegisOpsControlPlaneService` method.'
  'The Phase 50.12.7 starting measurements for `control-plane/aegisops_control_plane/service.py` are:'
  '- `physical_lines=1451`'
  '- `effective_lines=1294`'
  '- `AegisOpsControlPlaneService methods=100`'
  '- `phase=50.12.7`'
  '- `issue=#1022`'
  'The Phase 50.13 target ceiling is `AegisOpsControlPlaneService <= 85` methods if caller evidence proves the reduction is safe.'
  'The long-term 50-method target remains out of scope for this ADR and requires later child issues with implementation evidence.'
  'A method may be rewired away from the facade only when no external API, HTTP surface, CLI surface, or documented compatibility caller depends on the facade entrypoint.'
  'A retained compatibility delegate must remain a narrow single-hop facade over an extracted authoritative boundary.'
  'Private guards may move only when the receiving collaborator already owns the authoritative record, scope, provenance, authentication, or lifecycle boundary that the guard enforces.'
  'Internal rewiring must preserve snapshot consistency for multi-record reads and all-or-nothing durable writes for logical mutations.'
  'AegisOps control-plane records remain authoritative workflow truth.'
  'Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, snapshots, DTOs, and helper-module output remain subordinate context.'
  'Run `bash scripts/verify-phase-50-13-public-facade-inventory-contract.sh`.'
  'Run `bash scripts/test-verify-phase-50-13-public-facade-inventory-contract.sh`.'
  'Run `bash scripts/verify-maintainability-hotspots.sh`.'
  'Run `bash scripts/test-verify-maintainability-hotspots.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1031 --config <supervisor-config-path>`.'
  '- No production code extraction is approved by this ADR.'
  '- No public API, runtime endpoint, CLI command, operator UI behavior, or durable-state side effect is changed.'
  '- No approval, execution, reconciliation, assistant, detection, external-evidence, restore, readiness, or operator authority behavior is changed.'
  '- No baseline refresh is approved before implementation evidence exists.'
  '- No subordinate source, projection, DTO, summary, helper-module output, or nearby metadata becomes authoritative workflow truth.'
)

allowed_categories=(
  "external API"
  "HTTP surface dependency"
  "CLI dependency"
  "internal-only"
  "test-only"
  "compatibility delegate"
  "private guard"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 50.13 public facade inventory contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${service_path}" ]]; then
  echo "Missing service facade source: ${service_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 50.13 public facade inventory heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fxq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 50.13 public facade inventory statement: ${phrase}" >&2
    exit 1
  fi
done

allowed_pattern="$(printf '%s\n' "${allowed_categories[@]}" | paste -sd '|' -)"

export PHASE50_13_DOC_PATH="${doc_path}"
export PHASE50_13_SERVICE_PATH="${service_path}"
export PHASE50_13_ALLOWED_PATTERN="${allowed_pattern}"

python3 - <<'PY'
from __future__ import annotations

import ast
import os
import pathlib
import re
import sys

doc_path = pathlib.Path(os.environ["PHASE50_13_DOC_PATH"])
service_path = pathlib.Path(os.environ["PHASE50_13_SERVICE_PATH"])
allowed = frozenset(os.environ["PHASE50_13_ALLOWED_PATTERN"].split("|"))

tree = ast.parse(service_path.read_text(encoding="utf-8"))
service_class = next(
    (
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "AegisOpsControlPlaneService"
    ),
    None,
)
if service_class is None:
    print("Missing AegisOpsControlPlaneService class.", file=sys.stderr)
    sys.exit(1)

service_methods = [
    child.name
    for child in service_class.body
    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
]

doc_text = doc_path.read_text(encoding="utf-8")
row_pattern = re.compile(
    r"^\| `(?P<method>[^`]+)` \| (?P<category>[^|]+) \| (?P<caller>[^|]+) \| (?P<policy>[^|]+) \|$",
    re.MULTILINE,
)
rows = {}
duplicates = set()
invalid_categories = []
for match in row_pattern.finditer(doc_text):
    method = match.group("method")
    category = match.group("category").strip()
    if method in rows:
        duplicates.add(method)
    rows[method] = category
    if category not in allowed:
        invalid_categories.append(f"{method}: {category}")

if duplicates:
    print(
        "Phase 50.13 inventory has duplicate method rows: "
        + ", ".join(sorted(duplicates)),
        file=sys.stderr,
    )
    sys.exit(1)

missing = [method for method in service_methods if method not in rows]
extra = sorted(set(rows) - set(service_methods))
if missing:
    print(
        "Phase 50.13 inventory is missing facade method rows: "
        + ", ".join(missing),
        file=sys.stderr,
    )
    sys.exit(1)
if extra:
    print(
        "Phase 50.13 inventory lists methods not present on AegisOpsControlPlaneService: "
        + ", ".join(extra),
        file=sys.stderr,
    )
    sys.exit(1)
if invalid_categories:
    print(
        "Phase 50.13 inventory uses unsupported categories: "
        + "; ".join(invalid_categories),
        file=sys.stderr,
    )
    sys.exit(1)

if len(service_methods) != 95:
    print(
        f"Phase 50.13 inventory expected 95 facade methods after the Phase 50.13.3 guard relocation slice, found {len(service_methods)}.",
        file=sys.stderr,
    )
    sys.exit(1)
if len(rows) != 95:
    print(
        f"Phase 50.13 inventory must classify exactly 95 facade methods after the Phase 50.13.3 guard relocation slice, found {len(rows)}.",
        file=sys.stderr,
    )
    sys.exit(1)

print(
    "Phase 50.13 public facade inventory classifies all 95 current service facade methods and records compatibility policy, authority non-goals, target ceiling, and validation commands."
)
PY
