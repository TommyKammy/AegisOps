#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-6-replay-to-notify-validation.md"

bash "${script_dir}/verify-phase-5-semantic-contract-validation.sh" "${repo_root}"
bash "${script_dir}/verify-phase-6-initial-telemetry-slice-doc.sh" "${repo_root}"
bash "${script_dir}/verify-windows-source-onboarding-assets.sh" "${repo_root}"
bash "${script_dir}/verify-phase-6-opensearch-detector-artifacts.sh" "${repo_root}"
bash "${script_dir}/verify-sigma-n8n-skeleton-validation.sh" "${repo_root}"
bash "${script_dir}/verify-runbook-doc.sh" "${repo_root}"

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing Phase 6 replay-to-notify validation record: ${validation_doc}" >&2
  exit 1
fi

required_phrases=(
  "# Phase 6 Replay-to-Notify Validation"
  "- Validation date: 2026-04-03"
  "- Validation scope: Selected Windows security and endpoint replay-to-notify slice from normalized replay input through notify-only analyst routing"
  "- Baseline references: \`docs/phase-5-semantic-contract-validation.md\`, \`docs/phase-6-initial-telemetry-slice.md\`, \`docs/runbook.md\`"
  "- Verification commands: \`bash scripts/verify-phase-5-semantic-contract-validation.sh\`, \`bash scripts/verify-phase-6-initial-telemetry-slice-doc.sh\`, \`bash scripts/verify-windows-source-onboarding-assets.sh\`, \`bash scripts/verify-phase-6-opensearch-detector-artifacts.sh\`, \`bash scripts/verify-sigma-n8n-skeleton-validation.sh\`, \`bash scripts/verify-runbook-doc.sh\`, \`bash scripts/verify-phase-6-replay-to-notify-validation.sh\`"
  "- Validation status: PASS"
  "## Reviewed Artifacts"
  "## Commands Executed"
  "## Evidence Reviewed"
  "## Result"
  "## Guardrail Review"
  "## Deviations"
  "Validated the success replay corpus only for the three selected Windows use cases: privileged group membership change, audit log cleared, and new local user created."
  "Confirmed the normalized replay input remains limited to synthetic or redacted review fixtures and preserves the Phase 5 evidence, provenance, and replay-readiness semantics."
  "Confirmed the selected Sigma rules remain reviewable single-event detections and match the staging-only OpenSearch detector artifacts without introducing unsupported translation behavior."
  "Confirmed the enrich workflow remains read-only, the notify workflow remains notify-only, and the reviewed path stops at analyst routing without approval bypass, write-capable connectors, or response execution."
  "Confirmed the reviewed slice remains business-hours oriented, staging-only, and suitable for analyst queue handling rather than production activation or autonomous action."
  "No unresolved hidden write behavior, uncontrolled activation path, or silent architecture drift was identified in the reviewed replay-to-notify slice."
  "No deviations found."
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

reviewed_artifacts=(
  "docs/phase-6-initial-telemetry-slice.md"
  "docs/source-families/windows-security-and-endpoint/onboarding-package.md"
  "ingest/replay/windows-security-and-endpoint/normalized/success.ndjson"
  "sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml"
  "sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"
  "sigma/curated/windows-security-and-endpoint/new-local-user-created.yml"
  "opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml"
  "opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml"
  "opensearch/detectors/windows-security-and-endpoint/new-local-user-created-staging.yaml"
  "n8n/workflows/aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json"
  "n8n/workflows/aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json"
  "docs/runbook.md"
)

for artifact in "${reviewed_artifacts[@]}"; do
  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}"; then
    echo "Validation record must list reviewed artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Phase 6 replay-to-notify validation record matches the approved slice evidence and guardrails."
