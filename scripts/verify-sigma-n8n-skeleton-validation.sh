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
  "The Sigma curated and suppressed directories preserve the approved distinction between future onboarding candidates and documented future suppression decisions."
  "Both directories remain placeholder-only and do not introduce live Sigma rule, suppression, exception, or decision content."
  "The tracked n8n workflow skeleton covers the approved alert ingest, enrich, approve, notify, and response categories."
  "Each category remains a placeholder-only directory with a \`.gitkeep\` marker, and no exported workflow, trigger, credential, or execution logic is present."
  "No reviewed Sigma asset introduces runnable detection behavior, and no reviewed n8n asset introduces runnable workflow behavior."
  "The current tracked assets remain documentation and placeholder markers only."
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
  "sigma/suppressed/README.md"
  "n8n/workflows/README.md"
  "n8n/workflows/aegisops_alert_ingest/.gitkeep"
  "n8n/workflows/aegisops_approve/.gitkeep"
  "n8n/workflows/aegisops_enrich/.gitkeep"
  "n8n/workflows/aegisops_notify/.gitkeep"
  "n8n/workflows/aegisops_response/.gitkeep"
)

for artifact in "${reviewed_artifacts[@]}"; do
  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}"; then
    echo "Validation document must list reviewed artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Sigma and n8n skeleton assets match the approved category structure and remain placeholder-safe."
