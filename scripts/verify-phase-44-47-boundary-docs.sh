#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

required_docs=(
  "docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md"
  "docs/phase-44-pilot-ingress-and-operator-surface-closure-validation.md"
  "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md"
  "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-validation.md"
  "docs/phase-46-approval-execution-reconciliation-operations-pack-boundary.md"
  "docs/phase-46-approval-execution-reconciliation-operations-pack-validation.md"
  "docs/phase-47-control-plane-responsibility-decomposition-boundary.md"
  "docs/phase-47-control-plane-responsibility-decomposition-validation.md"
)

boundary_docs=(
  "docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md"
  "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md"
  "docs/phase-46-approval-execution-reconciliation-operations-pack-boundary.md"
  "docs/phase-47-control-plane-responsibility-decomposition-boundary.md"
)

validation_docs=(
  "docs/phase-44-pilot-ingress-and-operator-surface-closure-validation.md"
  "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-validation.md"
  "docs/phase-46-approval-execution-reconciliation-operations-pack-validation.md"
  "docs/phase-47-control-plane-responsibility-decomposition-validation.md"
)

non_goals_doc="docs/non-goals-and-expansion-guardrails.md"
readme_doc="README.md"

require_file() {
  local relative_path="$1"

  if [[ ! -s "${repo_root}/${relative_path}" ]]; then
    echo "Missing required Phase 44-47 boundary or validation doc: ${relative_path}" >&2
    exit 1
  fi
}

require_phrase() {
  local relative_path="$1"
  local phrase="$2"
  local description="$3"

  if [[ ! -f "${repo_root}/${relative_path}" ]]; then
    echo "Missing required navigation document for Phase 44-47 docs: ${relative_path}" >&2
    exit 1
  fi

  if ! grep -Fq -- "${phrase}" "${repo_root}/${relative_path}"; then
    echo "Missing ${description} in ${relative_path}: ${phrase}" >&2
    exit 1
  fi
}

for doc in "${required_docs[@]}"; do
  require_file "${doc}"
done

for doc in "${boundary_docs[@]}"; do
  require_phrase "${non_goals_doc}" "${doc}" "Phase 44-47 boundary cross-link"
  require_phrase "${readme_doc}" "${doc}" "Phase 44-47 handoff cross-link"
done

for doc in "${validation_docs[@]}"; do
  require_phrase "${readme_doc}" "${doc}" "Phase 44-47 validation handoff cross-link"
done

required_navigation_phrases=(
  "Phase 44-47 closure contracts"
  "Phase 44-47 boundary docs"
  "Phase 44-47 validation docs"
  "AegisOps control-plane records remain authoritative"
  "operator UI, proxy, Zammad, assistant, optional evidence, downstream receipts, and maintainability projections remain subordinate context"
)

for phrase in "${required_navigation_phrases[@]}"; do
  require_phrase "${readme_doc}" "${phrase}" "Phase 44-47 handoff summary"
done

required_guardrail_phrases=(
  "Phase 44-47 Closed Pilot-Readiness Guardrails"
  "pilot ingress, daily SOC queue, approval/execution/reconciliation operations, and control-plane responsibility decomposition"
  "AegisOps control-plane records remain authoritative"
  "No later roadmap item may use these closed phases to infer new runtime behavior, browser authority, ticket authority, assistant authority, optional-evidence authority, or commercial-readiness claims."
)

for phrase in "${required_guardrail_phrases[@]}"; do
  require_phrase "${non_goals_doc}" "${phrase}" "Phase 44-47 guardrail summary"
done

echo "Phase 44-47 boundary and validation docs are present and discoverable."
