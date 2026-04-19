#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
design_doc="${repo_root}/docs/phase-28-optional-endpoint-evidence-pack-boundary.md"
validation_doc="${repo_root}/docs/phase-28-optional-endpoint-evidence-pack-boundary-validation.md"
docs_test="${repo_root}/control-plane/tests/test_phase28_endpoint_evidence_pack_boundary_docs.py"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_line() {
  local path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${path}" >/dev/null; then
    echo "Missing required line in ${path}: ${expected}" >&2
    exit 1
  fi
}

require_file "${design_doc}" "Missing Phase 28 endpoint evidence-pack boundary doc"
require_file "${validation_doc}" "Missing Phase 28 endpoint evidence-pack boundary validation doc"
require_file "${docs_test}" "Missing Phase 28 endpoint evidence-pack doc unittest"

design_required_lines=(
  '# AegisOps Phase 28 Optional Endpoint Evidence-Pack Boundary'
  '## 1. Purpose'
  '## 2. Reviewed Optional Endpoint Evidence-Pack Role'
  '## 3. Enablement Conditions'
  '## 4. Approved Artifact Classes'
  '## 5. Provenance and Citation Requirements'
  '## 6. Tool-Specific Boundary Notes'
  '## 7. Non-Goals and Fail-Closed Rules'
  '## 8. Repository-Local Verification Commands'
  'This document defines the reviewed optional endpoint evidence-pack boundary for Phase 28.'
  'Velociraptor is approved only as a subordinate read and evidence-collection substrate for this slice.'
  'YARA and capa are approved only as subordinate evidence-pack analysis tools for collected files or binaries inside this same boundary.'
  'Endpoint evidence packs are optional augmentation, not a mandatory platform dependency or case-truth authority surface.'
  'A reviewed endpoint evidence pack may be used only when an existing operating need or explicit evidence gap is already present on the reviewed case chain.'
  'Endpoint evidence collection must start from an existing AegisOps-owned case, evidence record, or reviewed follow-up decision rather than from free-form endpoint hunting.'
  'The approved artifact classes for this boundary are:'
  '- `collection_manifest` for the reviewed description of what was requested, from which explicitly bound host, by which reviewed operator, and under which case or evidence anchor;'
  '- `triage_bundle` for bounded read-only host-state output such as reviewed process, service, autorun, user, scheduled-task, or network-observation snapshots tied to the scoped host;'
  '- `file_sample` for a reviewed collected file or bounded file subset taken from the scoped host or evidence path;'
  '- `binary_analysis` for derived YARA or capa findings over a reviewed collected file or binary sample; and'
  '- `tool_output_receipt` for the subordinate receipt that records which reviewed collector or analysis tool produced which artifact and when.'
  'Every collected or derived artifact must preserve provenance that identifies the source host binding, collector or tool identity, collection or analysis time, reviewed operator attribution, and the AegisOps evidence record that admitted it.'
  'Collected endpoint artifacts and derived YARA or capa outputs must be cited as subordinate evidence linked to an AegisOps-owned evidence record.'
  'Endpoint evidence packs must not replace AegisOps-owned case truth, actor truth, approval truth, or reconciliation truth.'
  'This boundary does not approve mandatory agent rollout, endpoint-first product repositioning, background fleet sweeps, autonomous collection, or endpoint-tool authority expansion.'
)

for line in "${design_required_lines[@]}"; do
  require_fixed_line "${design_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 28 Optional Endpoint Evidence-Pack Boundary Validation'
  '- Validation status: PASS'
  '- Reviewed on: 2026-04-19'
  '## Validation Summary'
  '## Roadmap and Thesis Review'
  '## Endpoint Evidence Boundary Review'
  '## Review Outcome'
  '## Verification'
  'Velociraptor remains subordinate to the AegisOps control-plane authority model.'
  'YARA and capa remain subordinate evidence-analysis tools rather than authority surfaces.'
  'Endpoint evidence packs remain optional, provenance-preserving, and fail closed when prerequisite case-chain linkage or provenance is incomplete.'
  '- Reviewed sources: `docs/Revised Phase23-20 Epic Roadmap.md` (repository-published roadmap anchor for the reviewed AegisOps thesis, SMB deployment target, and later source-expansion guardrails), `docs/requirements-baseline.md`, `docs/architecture.md`, `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md`, `docs/phase-25-multi-source-case-review-and-osquery-evidence-runbook.md`, `docs/phase-28-optional-endpoint-evidence-pack-boundary.md`'
  '- `python3 -m unittest control-plane.tests.test_phase28_endpoint_evidence_pack_boundary_docs`'
  '- `bash scripts/verify-phase-28-endpoint-evidence-pack-boundary.sh`'
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_line "${validation_doc}" "${line}"
done

require_fixed_line "${docs_test}" 'class Phase28EndpointEvidencePackBoundaryDocsTests(unittest.TestCase):'
require_fixed_line "${docs_test}" '    def test_phase28_design_doc_exists_and_keeps_endpoint_evidence_subordinate('
require_fixed_line "${docs_test}" '    def test_phase28_validation_doc_records_roadmap_and_baseline_review(self) -> None:'

echo "Phase 28 endpoint evidence-pack boundary documents are present and aligned."
