#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-25-multi-source-case-review-and-osquery-evidence-runbook.md"

required_headings=(
  "# Phase 25 Multi-Source Case Review and Osquery Evidence Runbook"
  "## 1. Purpose"
  "## 2. Scope and Non-Goals"
  "## 3. Business-Hours Multi-Source Case Review Checklist"
  "## 4. Osquery-Backed Host Evidence Handling"
  "## 5. Provenance and Ambiguity Interpretation"
  "## 6. Escalation and Out-of-Scope Boundaries"
  "## 7. Repository-Local Verification Commands"
)

required_phrases=(
  "This runbook defines the reviewed operator procedure for Phase 25 business-hours operator casework."
  'It supplements `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md`, `docs/source-families/github-audit/analyst-triage-runbook.md`, `docs/source-families/entra-id/analyst-triage-runbook.md`, `docs/secops-business-hours-operating-model.md`, and `docs/wazuh-rule-lifecycle-runbook.md`.'
  "The goal is to give operators one consistent procedure for multi-source case review, osquery-backed host evidence review, provenance interpretation, and ambiguity escalation without widening the reviewed authority model."
  "This runbook does not authorize broad entity stitching, substrate-led investigation, external substrate authority promotion, direct GitHub or Entra ID actioning, or free-form host hunting outside the reviewed case chain."
  "osquery-backed host evidence may add host, process, or local-state context, but it must not become the authority for case identity, actor identity, approval truth, or lifecycle truth on its own."
  "Operators should use the approved read-only inspection surfaces for this review:"
  '- `python3 control-plane/main.py inspect-case-detail --case-id <case-id>`'
  '- `python3 control-plane/main.py inspect-assistant-context --family case --record-id <case-id>`'
  'osquery-backed host evidence is admissible only when the reviewed case already binds the host explicitly through `reviewed_context.asset.host_identifier`.'
  'The approved osquery result kinds for this reviewed path are `host_state`, `process`, `local_user`, and `scheduled_query`.'
  "The operator reviews osquery-backed host evidence as augmenting evidence:"
  "The reviewed ambiguity states for this runbook are:"
  'Operators must not override an `unresolved` case detail state with a stronger assistant-facing interpretation unless a new authoritative reviewed link is recorded first.'
  "This runbook keeps broad entity stitching, substrate-led investigation, and external substrate authority explicitly out of scope for the reviewed Phase 25 path."
  "The repository-local verification commands for this runbook are:"
  '- `bash scripts/verify-phase-25-multi-source-case-review-runbook.sh`'
  '- `python3 -m unittest control-plane.tests.test_phase25_multi_source_case_admission_docs`'
  '- `python3 -m unittest control-plane.tests.test_phase25_osquery_host_context_validation`'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 25 multi-source case review runbook: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 25 runbook heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 25 runbook statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Phase 25 multi-source case review runbook is present and preserves the reviewed operator boundary."
