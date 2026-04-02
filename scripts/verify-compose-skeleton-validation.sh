#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
naming_guide_path="${repo_root}/docs/contributor-naming-guide.md"
validation_doc_path="${repo_root}/docs/compose-skeleton-validation.md"

compose_files=(
  "opensearch/docker-compose.yml"
  "n8n/docker-compose.yml"
  "proxy/docker-compose.yml"
  "ingest/docker-compose.yml"
)

expected_project_names=(
  "opensearch/docker-compose.yml:name: aegisops-opensearch"
  "n8n/docker-compose.yml:name: aegisops-n8n"
  "proxy/docker-compose.yml:name: aegisops-proxy"
  "ingest/docker-compose.yml:name: aegisops-ingest"
)

expected_service_names=(
  "opensearch/docker-compose.yml:opensearch"
  "opensearch/docker-compose.yml:dashboards"
  "n8n/docker-compose.yml:n8n"
  "proxy/docker-compose.yml:proxy"
  "ingest/docker-compose.yml:collector"
  "ingest/docker-compose.yml:parser"
)

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_pattern() {
  local path="$1"
  local pattern="$2"
  local message="$3"

  if ! grep -Eq -- "${pattern}" "${path}"; then
    echo "${message}" >&2
    exit 1
  fi
}

require_fixed_string() {
  local path="$1"
  local expected="$2"
  local message="$3"

  if ! grep -Fqx -- "${expected}" "${path}"; then
    echo "${message}" >&2
    exit 1
  fi
}

require_fixed_fragment() {
  local path="$1"
  local expected="$2"
  local message="$3"

  if ! grep -Fq -- "${expected}" "${path}"; then
    echo "${message}" >&2
    exit 1
  fi
}

require_file "${naming_guide_path}" "Missing contributor naming guide"
require_file "${validation_doc_path}" "Missing compose skeleton validation result document"

for compose_file in "${compose_files[@]}"; do
  require_file "${repo_root}/${compose_file}" "Missing compose skeleton"
done

for expected_name in \
  "aegisops-opensearch" \
  "aegisops-n8n" \
  "aegisops-ingest" \
  "aegisops-proxy"; do
  require_fixed_fragment \
    "${naming_guide_path}" \
    "\`${expected_name}\`" \
    "Contributor naming guide must include approved Compose project example ${expected_name}."
done

for project_entry in "${expected_project_names[@]}"; do
  compose_file="${project_entry%%:*}"
  expected_line="${project_entry#*:}"
  require_fixed_string \
    "${repo_root}/${compose_file}" \
    "${expected_line}" \
    "${compose_file} must use approved Compose project names from the contributor naming guide."
done

for service_entry in "${expected_service_names[@]}"; do
  compose_file="${service_entry%%:*}"
  service_name="${service_entry#*:}"
  require_fixed_string \
    "${repo_root}/${compose_file}" \
    "  ${service_name}:" \
    "${compose_file} must use approved service names aligned to the checked skeleton examples."
done

if grep -REn '^([[:space:]]*)image:[[:space:]]+[^[:space:]]+:latest$' \
  "${repo_root}/opensearch" \
  "${repo_root}/n8n" \
  "${repo_root}/proxy" \
  "${repo_root}/ingest" >/dev/null; then
  echo "Checked compose artifacts must not use the latest tag." >&2
  exit 1
fi

require_fixed_string "${validation_doc_path}" "# Compose Skeleton Validation" \
  "Compose skeleton validation document must use the approved title."
require_pattern "${validation_doc_path}" '^- Validation date: [0-9]{4}-[0-9]{2}-[0-9]{2}$' \
  "Compose skeleton validation document must record a validation date."
require_fixed_string "${validation_doc_path}" "- Baseline references: \`docs/contributor-naming-guide.md\`, \`docs/requirements-baseline.md\`" \
  "Compose skeleton validation document must cite the naming guide and requirements baseline."
require_fixed_string "${validation_doc_path}" "- Verification command: \`bash scripts/verify-compose-skeleton-validation.sh\`" \
  "Compose skeleton validation document must record the verification command."
require_fixed_string "${validation_doc_path}" "- Validation status: PASS" \
  "Compose skeleton validation document must record a PASS status."
require_fixed_string "${validation_doc_path}" "## Reviewed Artifacts" \
  "Compose skeleton validation document must list reviewed artifacts."
require_fixed_string "${validation_doc_path}" "## Naming Review Result" \
  "Compose skeleton validation document must summarize the naming review."
require_fixed_string "${validation_doc_path}" "## Image Tag Review Result" \
  "Compose skeleton validation document must summarize the image tag review."
require_fixed_string "${validation_doc_path}" "## Deviations" \
  "Compose skeleton validation document must include a deviations section."

for artifact in "${compose_files[@]}"; do
  require_fixed_string "${validation_doc_path}" "- \`${artifact}\`" \
    "Compose skeleton validation document must list ${artifact} as reviewed."
done

require_fixed_fragment "${validation_doc_path}" "approved \`aegisops-\` namespace examples" \
  "Compose skeleton validation document must record the approved Compose project naming result."
require_fixed_fragment "${validation_doc_path}" "\`opensearch\`, \`dashboards\`, \`n8n\`, \`proxy\`, \`collector\`, and \`parser\`" \
  "Compose skeleton validation document must record the reviewed service names."
require_fixed_fragment "${validation_doc_path}" "No checked compose artifact uses the \`latest\` image tag." \
  "Compose skeleton validation document must record the image tag review result."
require_fixed_string "${validation_doc_path}" "- No deviations found." \
  "Compose skeleton validation document must explicitly record the deviation outcome."

echo "Compose skeleton validation matches the approved naming and image-tag review record."
