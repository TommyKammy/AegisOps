#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-5-semantic-contract-validation.md"

bash "${repo_root}/scripts/verify-canonical-telemetry-schema-doc.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-secops-domain-model-doc.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-detection-lifecycle-and-rule-qa-framework.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-response-action-safety-model-doc.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-control-plane-state-model-doc.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-secops-business-hours-operating-model-doc.sh" "${repo_root}"

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing Phase 5 semantic contract validation result document: ${validation_doc}" >&2
  exit 1
fi

required_phrases=(
  "# Phase 5 Semantic Contract Validation"
  "- Validation date:"
  "- Validation scope: Telemetry schema, SecOps domain semantics, detection lifecycle, approval binding, control-plane state, and business-hours operating model"
  "- Baseline references: \`docs/requirements-baseline.md\`, \`docs/architecture.md\`, \`docs/runbook.md\`"
  "- \`docs/canonical-telemetry-schema-baseline.md\`"
  "- \`docs/secops-domain-model.md\`"
  "- \`docs/detection-lifecycle-and-rule-qa-framework.md\`"
  "- \`docs/response-action-safety-model.md\`"
  "- \`docs/control-plane-state-model.md\`"
  "- \`docs/secops-business-hours-operating-model.md\`"
  "- Verification commands: \`bash scripts/verify-canonical-telemetry-schema-doc.sh\`, \`bash scripts/verify-secops-domain-model-doc.sh\`, \`bash scripts/verify-detection-lifecycle-and-rule-qa-framework.sh\`, \`bash scripts/verify-response-action-safety-model-doc.sh\`, \`bash scripts/verify-control-plane-state-model-doc.sh\`, \`bash scripts/verify-secops-business-hours-operating-model-doc.sh\`, \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`"
  "- Validation status: PASS"
  "Confirmed the telemetry contract stays schema-only and ECS-aligned rather than implying live mappings, ingest transforms, or new retention behavior."
  "Confirmed detection content remains review- and evidence-bound and does not silently authorize production activation, staging bypass, or response execution."
  "Confirmed approval, action request, and action execution remain separate first-class records with approval-bound write safeguards."
  "Confirmed control-plane ownership remains distinct from OpenSearch analytics outputs and n8n execution history and does not introduce a new live datastore or exposed service boundary."
  "Confirmed the operating model remains business-hours-oriented, preserves explicit human escalation and approval decisions, and does not imply 24x7 staffing or autonomous destructive response."
  "The reviewed Phase 5 semantic-contract documents remain aligned with the approved requirements baseline, architecture overview, and runbook skeleton."
  "Telemetry, detection, approval, control-plane, and operating-model terminology remain consistent about record boundaries, evidence expectations, and the separation between analytics, approval, and execution."
  "The reviewed artifacts do not silently authorize live detection rollout, uncontrolled write behavior, new exposed service boundaries, or runtime implementation beyond the approved baseline."
  "No deviations found."
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

echo "Phase 5 semantic contract validation record matches the approved baseline checks."
