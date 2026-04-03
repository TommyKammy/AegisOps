#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/sigma-n8n-skeleton-validation.md"

bash "${script_dir}/verify-sigma-guidance-doc.sh" "${repo_root}"
bash "${script_dir}/verify-sigma-curated-skeleton.sh" "${repo_root}"
bash "${script_dir}/verify-sigma-suppressed-skeleton.sh" "${repo_root}"
bash "${script_dir}/verify-n8n-workflow-category-guidance.sh" "${repo_root}"
bash "${script_dir}/verify-n8n-workflow-skeleton.sh" "${repo_root}"

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing Sigma and n8n skeleton validation result document: ${validation_doc}" >&2
  exit 1
fi

required_phrases=(
  "# Sigma and n8n Skeleton Asset Validation"
  "- Validation date:"
  "- Baseline references: \`docs/requirements-baseline.md\`, \`docs/repository-structure-baseline.md\`, \`sigma/README.md\`, \`n8n/workflows/README.md\`"
  "- Verification commands: \`bash scripts/verify-sigma-guidance-doc.sh\`, \`bash scripts/verify-sigma-curated-skeleton.sh\`, \`bash scripts/verify-sigma-suppressed-skeleton.sh\`, \`bash scripts/verify-n8n-workflow-category-guidance.sh\`, \`bash scripts/verify-n8n-workflow-skeleton.sh\`, \`bash scripts/verify-sigma-n8n-skeleton-validation.sh\`"
  "- Validation status: PASS"
  "## Reviewed Artifacts"
  "## Sigma Review Result"
  "## n8n Workflow Category Review Result"
  "## Live Behavior Review Result"
  "## Deviations"
  "The Sigma curated and suppressed directories preserve the approved distinction between reviewed onboarding candidates and documented future suppression decisions."
  "The curated slice is limited to privileged group membership change, audit log cleared, and new local user created, and the suppressed directory remains placeholder-only without live suppression entries."
  "The tracked n8n workflow structure keeps the approved alert ingest, enrich, approve, notify, and response categories while limiting exported workflow assets to the selected Phase 6 read-only slice."
  "Alert ingest, approve, and response remain placeholder-only with \`.gitkeep\` markers, while enrich and notify contain only the approved selected-detector workflow exports."
  "No reviewed Sigma asset introduces runnable detection behavior, and the reviewed n8n assets remain read-only workflow exports without approval-exempt write or response execution steps."
  "The current tracked Sigma assets remain reviewed content only, and the n8n workflow assets are limited to enrichment, routing, and notification payload preparation for the selected Windows detector outputs."
  "No deviations found."
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

reviewed_artifacts=(
  "sigma/README.md"
  "sigma/curated/README.md"
  "sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"
  "sigma/curated/windows-security-and-endpoint/new-local-user-created.yml"
  "sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml"
  "sigma/suppressed/README.md"
  "n8n/workflows/README.md"
  "n8n/workflows/aegisops_alert_ingest/.gitkeep"
  "n8n/workflows/aegisops_approve/.gitkeep"
  "n8n/workflows/aegisops_enrich/.gitkeep"
  "n8n/workflows/aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json"
  "n8n/workflows/aegisops_notify/.gitkeep"
  "n8n/workflows/aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json"
  "n8n/workflows/aegisops_response/.gitkeep"
)

for artifact in "${reviewed_artifacts[@]}"; do
  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}"; then
    echo "Validation document must list reviewed artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Sigma assets remain reviewed content and n8n assets remain limited to the approved Phase 6 read-only workflow slice."
