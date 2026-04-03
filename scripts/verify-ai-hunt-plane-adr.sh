#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md"

required_headings=(
  "# ADR-0001: Phase 7 AI Hunt Plane and External AI Data Boundary"
  "## 1. Context"
  "## 2. Decision"
  "## 3. Decision Drivers"
  "## 4. Options Considered"
  "## 5. Rationale"
  "## 6. Consequences"
  "## 7. Implementation Impact"
  "## 8. Security Impact"
  "## 9. Rollback / Exit Strategy"
  "## 10. Validation"
  "## 11. Non-Goals"
  "## 12. Approval"
)

required_phrases=(
  "- **Status**: Accepted"
  "The AI hunt plane is an advisory-only analysis surface."
  "The AI hunt plane must not become a shadow control plane."
  "The AI hunt plane may read approved source material from the detection plane and the control plane, but it does not own alert, case, approval, or execution state."
  "Direct AI-to-n8n execution is prohibited."
  "External AI output must never be treated as evidence by itself."
  'Every external AI request must use `store=false` or an equivalent provider control that disables provider-side retention and training use.'
  '| Sanitized detection summary | Allowed with reviewable prompt context | External AI may receive analyst-prepared summaries of findings, detections, and hypotheses when direct identifiers, secrets, and raw event payloads are removed. |'
  '| Case narrative, approval state, or action-execution state | Prohibited | External AI must not become the system of record or working memory for operator workflow state. |'
  '| Secrets, credentials, tokens, private keys, session cookies, or live approval artifacts | Prohibited | These classes remain internal-only because disclosure could directly widen authority or bypass approval boundaries. |'
  "The AI hunt plane may recommend hunts, summarize patterns, propose Sigma-style logic, and rank follow-up questions, but a human analyst must decide whether any recommendation changes alert, case, approval, or execution state."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing AI hunt plane ADR: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing AI hunt plane ADR heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing AI hunt plane ADR statement: ${phrase}" >&2
    exit 1
  fi
done

echo "AI hunt plane ADR is present and defines advisory-only AI boundaries plus the external AI data policy."
