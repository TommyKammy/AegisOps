#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/opensearch-placeholder-and-detector-validation.md"

bash "${repo_root}/scripts/verify-opensearch-index-template-placeholders.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-opensearch-detector-metadata-template.sh" "${repo_root}"

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing OpenSearch placeholder and detector validation result document: ${validation_doc}" >&2
  exit 1
fi

required_phrases=(
  "# OpenSearch Placeholder and Detector Validation"
  "- Validation date:"
  "- Baseline references: \`docs/contributor-naming-guide.md\`, \`docs/requirements-baseline.md\`, \`docs/repository-structure-baseline.md\`, \`opensearch/index-templates/README.md\`, \`opensearch/detectors/README.md\`"
  "- Verification commands: \`bash scripts/verify-opensearch-index-template-placeholders.sh\`, \`bash scripts/verify-opensearch-detector-metadata-template.sh\`, \`bash scripts/verify-opensearch-placeholder-and-detector-validation.sh\`"
  "- Validation status: PASS"
  "## Reviewed Artifacts"
  "## Index Template Naming Review Result"
  "## Detector Metadata Review Result"
  "## Deviations"
  "The placeholder assets under \`opensearch/index-templates/\` use the approved \`aegisops-logs-<family>-*\` naming baseline for the current Windows, Linux, network, and SaaS log families."
  "The detector metadata template remains placeholder-only and includes the required detector name pattern, owner, purpose, severity, expected behavior, MITRE ATT&CK technique tags, source prerequisites, and false-positive considerations."
  "No deviations found."
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

reviewed_artifacts=(
  "opensearch/index-templates/README.md"
  "opensearch/index-templates/aegisops-logs-linux-template.json"
  "opensearch/index-templates/aegisops-logs-network-template.json"
  "opensearch/index-templates/aegisops-logs-saas-template.json"
  "opensearch/index-templates/aegisops-logs-windows-template.json"
  "opensearch/detectors/README.md"
  "opensearch/detectors/aegisops-detector-metadata-template.yaml"
)

for artifact in "${reviewed_artifacts[@]}"; do
  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}"; then
    echo "Validation document must list reviewed artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "OpenSearch placeholder and detector validation record matches the approved naming and metadata review."
