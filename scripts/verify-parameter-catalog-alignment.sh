#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docs_dir="${repo_root}/docs/parameters"
config_dir="${repo_root}/config/parameters"
validation_doc="${repo_root}/docs/parameter-catalog-validation.md"

approved_categories=(
  "network"
  "compute"
  "storage"
  "platform"
  "security"
  "operations"
)

doc_required_phrases=(
  "This placeholder document exists to reserve the approved"
  "parameter category for future AegisOps catalog entries."
  "It describes category purpose only."
  "No production values, environment-specific settings, or secrets belong in this file."
)

config_required_phrases=(
  "schema_version: 1"
  "status: placeholder"
  "non_secret: true"
  "environment: template"
  "values: {}"
)

if [[ ! -d "${docs_dir}" ]]; then
  echo "Missing parameter docs directory: ${docs_dir}" >&2
  exit 1
fi

if [[ ! -d "${config_dir}" ]]; then
  echo "Missing parameter config directory: ${config_dir}" >&2
  exit 1
fi

for category in "${approved_categories[@]}"; do
  doc_path="${docs_dir}/${category}-parameters.md"
  config_path="${config_dir}/${category}.yaml"

  if [[ ! -f "${doc_path}" ]]; then
    echo "Missing parameter category document: ${doc_path}" >&2
    exit 1
  fi

  if [[ ! -f "${config_path}" ]]; then
    echo "Missing parameter config file: ${config_path}" >&2
    exit 1
  fi

  if ! grep -Eq '^# AegisOps .+ Parameters$' "${doc_path}"; then
    echo "Missing parameter document title in ${doc_path}" >&2
    exit 1
  fi

  for phrase in "${doc_required_phrases[@]}"; do
    if ! grep -Fq "${phrase}" "${doc_path}"; then
      echo "Missing placeholder statement in ${doc_path}: ${phrase}" >&2
      exit 1
    fi
  done

  if grep -Eiq '(^|[^[:alnum:]_])\.env([^[:alnum:]_]|$)|BEGIN [A-Z ]+PRIVATE KEY|AKIA[0-9A-Z]{16}' "${doc_path}"; then
    echo "Potential active environment or secret material detected in ${doc_path}" >&2
    exit 1
  fi

  if ! grep -Fxq "category: ${category}" "${config_path}"; then
    echo "Missing category marker in ${config_path}" >&2
    exit 1
  fi

  for phrase in "${config_required_phrases[@]}"; do
    if ! grep -Fq "${phrase}" "${config_path}"; then
      echo "Missing placeholder field in ${config_path}: ${phrase}" >&2
      exit 1
    fi
  done

  if grep -Eiq '(^|[^[:alnum:]_])\.env([^[:alnum:]_]|$)|BEGIN [A-Z ]+PRIVATE KEY|AKIA[0-9A-Z]{16}' "${config_path}"; then
    echo "Potential active environment or secret material detected in ${config_path}" >&2
    exit 1
  fi
done

doc_count="$(find "${docs_dir}" -maxdepth 1 -type f -name '*-parameters.md' | wc -l | tr -d '[:space:]')"
config_count="$(find "${config_dir}" -maxdepth 1 -type f -name '*.yaml' | wc -l | tr -d '[:space:]')"

if [[ "${doc_count}" -ne "${#approved_categories[@]}" ]]; then
  echo "Unexpected parameter document count in ${docs_dir}: ${doc_count}" >&2
  exit 1
fi

if [[ "${config_count}" -ne "${#approved_categories[@]}" ]]; then
  echo "Unexpected parameter config count in ${config_dir}: ${config_count}" >&2
  exit 1
fi

if find "${docs_dir}" "${config_dir}" -maxdepth 1 -type f -name '.env*' | grep -q .; then
  echo "Active .env file detected in parameter catalog locations" >&2
  exit 1
fi

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing parameter catalog validation result document: ${validation_doc}" >&2
  exit 1
fi

validation_required_phrases=(
  "# Parameter Catalog Validation"
  "- Validation date:"
  "- Baseline reference: \`docs/parameters/environment-parameter-catalog-structure.md\`"
  "- Verification command: \`bash scripts/verify-parameter-catalog-alignment.sh\`"
  "- Validation status: PASS"
  "The parameter catalog locations and category coverage align with the approved AegisOps structure."
)

for phrase in "${validation_required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

echo "Parameter catalog locations, category coverage, and validation record align with the approved structure."
