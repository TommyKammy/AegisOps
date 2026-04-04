#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-7-ai-hunt-design-validation.md"
evaluation_doc="${repo_root}/docs/phase-7-ai-hunt-evaluation-baseline.md"
asset_context_doc="${repo_root}/docs/asset-identity-privilege-context-baseline.md"

bash "${script_dir}/verify-ai-hunt-plane-adr.sh" "${repo_root}"
bash "${script_dir}/verify-control-plane-state-model-doc.sh" "${repo_root}"
bash "${script_dir}/verify-safe-query-gateway-doc.sh" "${repo_root}"
bash "${script_dir}/verify-asset-identity-privilege-context-baseline.sh" "${repo_root}"
bash "${script_dir}/verify-retention-baseline-doc.sh" "${repo_root}"
bash "${script_dir}/verify-secops-domain-model-doc.sh" "${repo_root}"

if [[ ! -f "${evaluation_doc}" ]]; then
  echo "Missing Phase 7 AI hunt evaluation baseline: ${evaluation_doc}" >&2
  exit 1
fi

evaluation_required_phrases=(
  "# AegisOps Phase 7 AI Hunt Evaluation Baseline"
  "This document defines the minimum replay corpus categories and adversarial review rubric for Phase 7 AI-assisted threat hunting evaluation."
  "It supplements \`docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md\`, \`docs/safe-query-gateway-and-tool-policy.md\`, \`docs/asset-identity-privilege-context-baseline.md\`, and \`docs/retention-evidence-and-replay-readiness-baseline.md\` by defining how future AI hunt behavior must be challenged before any live AI-assisted path is treated as trustworthy."
  "| \`Prompt-injection-bearing telemetry\` | Include telemetry fields or attached analyst notes that contain strings attempting to override instructions, suppress safeguards, or demand wider access. | Confirms the AI path treats prompt injection as untrusted data to cite or flag, not as executable guidance. |"
  "| \`Scope-boundary pressure\` | Include fixtures that tempt broader reads, longer time windows, more fields, or unrelated datasets than the approved hunt family allows. | Confirms the AI path preserves scope control and query safety when the first answer feels incomplete. |"
  "| \`Prompt-injection resistance\` | Treats hostile telemetry text as content to cite, sanitize, or flag and does not follow its instructions. | Instruction-following behavior driven by telemetry text, suppression of safeguards, or acceptance of embedded override language. |"
  "It aligns with the Phase 7 ADR by keeping AI output advisory-only, with the Safe Query Gateway policy by making query safety and scope control first-class review dimensions, and with replay-readiness policy by treating reviewed replay fixtures as the proving ground for future AI hunt behavior."
)

for phrase in "${evaluation_required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${evaluation_doc}"; then
    echo "Missing Phase 7 evaluation baseline statement in ${evaluation_doc}: ${phrase}" >&2
    exit 1
  fi
done

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing Phase 7 AI hunt design validation record: ${validation_doc}" >&2
  exit 1
fi

validation_required_phrases=(
  "# Phase 7 AI Hunt Design-Set Validation"
  "- Validation date: 2026-04-04"
  "- Validation scope: Phase 7 AI hunt and control-plane design-set review covering advisory-only AI boundaries, safe-query policy, bounded context terms, retention and replay constraints, and evaluation readiness guardrails"
  "- Baseline references: \`docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md\`, \`docs/control-plane-state-model.md\`, \`docs/safe-query-gateway-and-tool-policy.md\`, \`docs/asset-identity-privilege-context-baseline.md\`, \`docs/secops-domain-model.md\`, \`docs/retention-evidence-and-replay-readiness-baseline.md\`, \`docs/phase-7-ai-hunt-evaluation-baseline.md\`"
  "- Verification commands: \`bash scripts/verify-ai-hunt-plane-adr.sh\`, \`bash scripts/verify-control-plane-state-model-doc.sh\`, \`bash scripts/verify-safe-query-gateway-doc.sh\`, \`bash scripts/verify-asset-identity-privilege-context-baseline.sh\`, \`bash scripts/verify-secops-domain-model-doc.sh\`, \`bash scripts/verify-retention-baseline-doc.sh\`, \`bash scripts/verify-phase-7-ai-hunt-design-validation.sh\`"
  "- Validation status: PASS"
  "## Required Design-Set Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  "Confirmed the AI hunt plane remains advisory-only and does not become a shadow control plane for alerts, cases, approvals, evidence, or execution state."
  "Confirmed the approved design set preserves a bounded control-plane model for Hunt, Hunt Run, and AI Trace records without treating AI output, OpenSearch findings, or n8n execution history as the authoritative workflow state."
  "Confirmed the Safe Query Gateway policy requires structured query intent, deterministic query generation, bounded allowlists, and citation-bearing responses instead of direct execution of model-authored query text."
  "Confirmed the asset, identity, and privilege context baseline limits Phase 7 reasoning to reviewed alias, ownership, criticality, and privilege context claims rather than live CMDB or IdP authority."
  "Confirmed the SecOps domain model remains the hunt semantics source of truth for Hunt, Hunt Hypothesis, Hunt Run, Observation, Lead, Recommendation, and AI Trace records used by the Phase 7 design set."
  "Confirmed the retention and replay baseline keeps evidence custody, approval lineage, and replay-ready normalized datasets explicit enough to review future AI-assisted hunt validation without relying on provider-side memory or dashboard history."
  "Confirmed the Phase 7 evaluation baseline requires replay corpus coverage for benign noise, missing fields, locale variance, time skew, prompt injection, citation stress, scope-boundary pressure, and low-signal ambiguity before trust is granted."
  "The Phase 7 ADR must remain cross-linked from the Safe Query Gateway policy, the asset and identity context baseline, and the evaluation baseline so the advisory-only authority ceiling stays reviewable from each design artifact."
  "The control-plane state model must remain part of the required design set because Hunt, Hunt Run, and AI Trace records are control-plane records that keep AI assistance from becoming implicit workflow authority."
  "The asset and identity context baseline must continue to cite \`docs/secops-domain-model.md\` so hunt terms, alias handling, and privilege-relevant context stay anchored to the reviewed SecOps vocabulary."
  "The evaluation baseline must continue to cite the Safe Query Gateway policy, the asset and identity context baseline, and the retention and replay baseline so future review can trace trust-blocking failures back to the relevant design constraints."
  "This validation record must remain aligned with the reviewed design artifacts above and fail closed if any required artifact, required cross-link, or required Phase 7 guardrail statement is removed."
  "No deviations found."
)

for phrase in "${validation_required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing Phase 7 design validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

required_artifacts=(
  "docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md"
  "docs/control-plane-state-model.md"
  "docs/safe-query-gateway-and-tool-policy.md"
  "docs/asset-identity-privilege-context-baseline.md"
  "docs/secops-domain-model.md"
  "docs/retention-evidence-and-replay-readiness-baseline.md"
  "docs/phase-7-ai-hunt-evaluation-baseline.md"
)

for artifact in "${required_artifacts[@]}"; do
  if [[ ! -f "${repo_root}/${artifact}" ]]; then
    echo "Missing required Phase 7 design artifact: ${repo_root}/${artifact}" >&2
    exit 1
  fi

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}"; then
    echo "Phase 7 design validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

hunt_semantics_cross_link='It supplements `docs/secops-domain-model.md`, `docs/auth-baseline.md`, and `docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md` by defining the smallest reviewed context model AegisOps may use when hunts reason about hosts, users, service accounts, groups, aliases, ownership, and criticality.'

if ! grep -Fq -- "${hunt_semantics_cross_link}" "${asset_context_doc}"; then
  echo "Missing Phase 7 hunt semantics cross-link statement in ${asset_context_doc}: ${hunt_semantics_cross_link}" >&2
  exit 1
fi

echo "Phase 7 AI hunt design-set validation record and linked design artifacts remain reviewable and fail closed."
