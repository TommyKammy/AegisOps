#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
design_doc="${repo_root}/docs/phase-29-optional-suricata-evidence-pack-boundary.md"
validation_doc="${repo_root}/docs/phase-29-optional-suricata-evidence-pack-boundary-validation.md"
docs_test="${repo_root}/control-plane/tests/test_phase29_suricata_evidence_pack_boundary_validation.py"

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

require_file "${design_doc}" "Missing Phase 29 Suricata evidence-pack boundary doc"
require_file "${validation_doc}" "Missing Phase 29 Suricata evidence-pack boundary validation doc"
require_file "${docs_test}" "Missing Phase 29 Suricata evidence-pack boundary unittest"

design_required_lines=(
  '# AegisOps Phase 29 Optional Suricata Evidence-Pack Boundary'
  '## 1. Purpose'
  '## 2. Reviewed Optional Suricata Role'
  '## 3. Enablement Conditions'
  '## 4. Approved Artifact Classes'
  '## 5. Provenance and Citation Requirements'
  '## 6. Boundary Notes for Phase 29 Shadow Mode'
  '## 7. Non-Goals and Fail-Closed Rules'
  '## 8. Repository-Local Verification Commands'
  'This document defines the reviewed optional Suricata evidence-pack boundary for Phase 29.'
  'Suricata integration is optional, disabled by default, and subordinate to the AegisOps-owned control-plane record chain.'
  'Suricata is approved only as a subordinate evidence-pack and shadow-correlation substrate for this reviewed slice.'
  'Suricata-derived output is optional augmentation, not a mandatory platform dependency or case-truth authority surface.'
  'A reviewed Suricata evidence pack may be used only when an existing operating need or explicit evidence gap is already present on the reviewed case chain.'
  'Suricata collection or parsing must start from an existing AegisOps-owned case, evidence record, or reviewed follow-up decision rather than from free-form network hunting or substrate-first alerting.'
  'The approved artifact classes for this boundary are:'
  '- `collection_manifest` for the reviewed description of which bounded Suricata source, observer, time window, and case or evidence anchor were requested;'
  '- `alert_sample` for the explicitly scoped Suricata alert or event material collected under the reviewed anchor;'
  '- `flow_excerpt` for the bounded flow, transaction, or protocol excerpt tied to the reviewed anchor rather than a broad sensor dump;'
  '- `shadow_correlation_note` for subordinate correlation context that may inform Phase 29 shadow-only comparison work without becoming workflow truth; and'
  '- `tool_output_receipt` for the subordinate receipt that records which reviewed Suricata source, parser, or import step produced which artifact and when.'
  'Every Suricata-derived artifact must preserve provenance that identifies the reviewed observer or sensor binding, source family, source event or flow identifier when available, bounded time window, reviewed operator or reviewed automation attribution, and the AegisOps evidence record that admitted it.'
  'Suricata-derived artifacts and shadow correlation notes must be cited as subordinate evidence linked to an AegisOps-owned evidence record.'
  'Suricata-derived output must not replace AegisOps-owned alert truth, case truth, evidence truth, approval truth, execution truth, or reconciliation truth.'
  'This boundary does not approve network-first mainline detection, broad IDS-led workflow redesign, mandatory Suricata deployment, or substrate authority expansion.'
)

for line in "${design_required_lines[@]}"; do
  require_fixed_line "${design_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 29 Optional Suricata Evidence-Pack Boundary Validation'
  '- Validation status: PASS'
  '- Reviewed on: 2026-04-20'
  '## Validation Summary'
  '## Thesis and Authority Review'
  '## Suricata Boundary Review'
  '## Phase 29 Shadow-Mode Review'
  '## Review Outcome'
  '## Verification'
  'The reviewed Suricata boundary remains optional, disabled by default, provenance-preserving, and fail closed when reviewed linkage or scope is incomplete.'
  'Suricata integration is optional, disabled by default, and subordinate to the AegisOps-owned control-plane record chain.'
  'Any Suricata-derived feature, note, or correlation signal must preserve explicit provenance and remain advisory-only.'
  'Suricata-derived output cannot become an authoritative label source and cannot silently promote network telemetry into mainline workflow truth.'
  'No reviewed language in this slice promotes network-first product positioning or broad IDS-led workflow redesign.'
  '- `python3 -m unittest control-plane.tests.test_phase29_suricata_evidence_pack_boundary_validation`'
  '- `bash scripts/verify-phase-29-suricata-evidence-pack-boundary.sh`'
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_line "${validation_doc}" "${line}"
done

require_fixed_line "${docs_test}" 'class Phase29SuricataEvidencePackBoundaryValidationTests(unittest.TestCase):'
require_fixed_line "${docs_test}" '    def test_phase29_suricata_design_doc_exists_and_keeps_suricata_subordinate('
require_fixed_line "${docs_test}" '    def test_phase29_suricata_validation_doc_records_boundary_and_shadow_mode_review('

echo "Phase 29 Suricata evidence-pack boundary documents are present and aligned."
