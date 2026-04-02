#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/architecture-runbook-validation.md"

bash "${repo_root}/scripts/verify-architecture-doc.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-runbook-doc.sh" "${repo_root}"

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing architecture and runbook validation result document: ${validation_doc}" >&2
  exit 1
fi

required_phrases=(
  "# Architecture and Runbook Validation"
  "- Validation date:"
  "- Baseline references: \`docs/architecture.md\`, \`docs/runbook.md\`, \`docs/requirements-baseline.md\`"
  "- Verification commands: \`bash scripts/verify-architecture-doc.sh\`, \`bash scripts/verify-runbook-doc.sh\`"
  "- Validation status: PASS"
  "The approved architecture overview and runbook skeleton remain aligned with the repository after the compose skeleton introduction."
  "No deviations found."
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

echo "Architecture and runbook validation record matches the approved baseline checks."
