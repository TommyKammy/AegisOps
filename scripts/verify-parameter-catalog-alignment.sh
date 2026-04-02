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

secret_pattern='(^|[^[:alnum:]_])\.env([^[:alnum:]_]|$)|BEGIN [A-Z ]+PRIVATE KEY|AKIA[0-9A-Z]{16}'

doc_category_description() {
  case "$1" in
    network)
      printf '%s\n' 'The `network` category will document hostnames, IP addressing, subnets, DNS dependencies, and approved service endpoints that operators must review before environment-specific implementation work.'
      ;;
    compute)
      printf '%s\n' 'The `compute` category will document node roles, sizing references, runtime capacity assumptions, and similar infrastructure-level identifiers that guide future deployment planning.'
      ;;
    storage)
      printf '%s\n' 'The `storage` category will document mount points, data paths, backup targets, persistence-related parameter names, and other storage references that reviewers need to assess safely.'
      ;;
    platform)
      printf '%s\n' 'The `platform` category will document component identifiers, Docker Compose project names, execution modes, retention defaults, and other product-level runtime settings in descriptive form.'
      ;;
    security)
      printf '%s\n' 'The `security` category will document TLS material references, secret identifier names, approval-related parameter names, and access-control-related configuration keys without exposing live credentials.'
      ;;
    operations)
      printf '%s\n' 'The `operations` category will document backup schedules, monitoring hooks, maintenance metadata, and other operator-facing control parameters that require reviewable documentation.'
      ;;
    *)
      echo "Unexpected parameter category: $1" >&2
      exit 1
      ;;
  esac
}

config_category_description() {
  case "$1" in
    network)
      printf '%s\n' 'Placeholder parameter catalog for non-production network settings.'
      ;;
    compute)
      printf '%s\n' 'Placeholder parameter catalog for non-production compute settings.'
      ;;
    storage)
      printf '%s\n' 'Placeholder parameter catalog for non-production storage settings.'
      ;;
    platform)
      printf '%s\n' 'Placeholder parameter catalog for non-production platform settings.'
      ;;
    security)
      printf '%s\n' 'Placeholder parameter catalog for non-production security metadata.'
      ;;
    operations)
      printf '%s\n' 'Placeholder parameter catalog for non-production operations settings.'
      ;;
    *)
      echo "Unexpected parameter category: $1" >&2
      exit 1
      ;;
  esac
}

contains_exact_line() {
  local needle="$1"
  shift

  local candidate
  for candidate in "$@"; do
    if [[ "${candidate}" == "${needle}" ]]; then
      return 0
    fi
  done

  return 1
}

category_title_from_doc_path() {
  local doc_name="${1##*/}"
  local category_slug="${doc_name%.md}"
  category_slug="${category_slug%-parameters}"

  local -a words=()
  local word
  IFS='-' read -r -a words <<< "${category_slug}"

  local title=""
  local first_char
  local rest
  for word in "${words[@]}"; do
    first_char="$(printf '%s' "${word:0:1}" | tr '[:lower:]' '[:upper:]')"
    rest="${word:1}"
    title+="${title:+ }${first_char}${rest}"
  done

  printf '%s\n' "${title}"
}

assert_exact_file_set() {
  local dir_path="$1"
  local label="$2"
  shift 2

  local -a expected_files=("$@")
  local -a expected_sorted=()
  local -a actual_sorted=()
  local path

  expected_sorted=($(printf '%s\n' "${expected_files[@]}" | LC_ALL=C sort))

  for path in "${dir_path}"/*; do
    if [[ -f "${path}" ]]; then
      actual_sorted+=("${path##*/}")
    fi
  done

  if [[ "${#actual_sorted[@]}" -gt 0 ]]; then
    actual_sorted=($(printf '%s\n' "${actual_sorted[@]}" | LC_ALL=C sort))
  fi

  if [[ "${#actual_sorted[@]}" -ne "${#expected_sorted[@]}" ]]; then
    echo "Unexpected ${label} file count in ${dir_path}" >&2
    echo "Expected ${label} files: ${expected_sorted[*]}" >&2
    echo "Actual ${label} files: ${actual_sorted[*]}" >&2
    exit 1
  fi

  local index
  for index in "${!expected_sorted[@]}"; do
    if [[ "${actual_sorted[${index}]}" != "${expected_sorted[${index}]}" ]]; then
      echo "Unexpected ${label} file set in ${dir_path}" >&2
      echo "Expected ${label} files: ${expected_sorted[*]}" >&2
      echo "Actual ${label} files: ${actual_sorted[*]}" >&2
      exit 1
    fi
  done
}

validate_placeholder_doc() {
  local category="$1"
  local doc_path="$2"
  local category_description

  category_description="$(doc_category_description "${category}")"

  local expected_title="# AegisOps $(category_title_from_doc_path "${doc_path}") Parameters"
  local actual_title
  actual_title="$(head -n 1 "${doc_path}")"

  if [[ "${actual_title}" != "${expected_title}" ]]; then
    echo "Unexpected parameter document title in ${doc_path}: ${actual_title}" >&2
    exit 1
  fi

  local -a allowed_lines=(
    "${expected_title}"
    "This placeholder document exists to reserve the approved \`${category}\` parameter category for future AegisOps catalog entries."
    "It describes category purpose only."
    "${category_description}"
    "No production values, environment-specific settings, or secrets belong in this file."
  )

  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ -z "${line}" ]]; then
      continue
    fi

    if [[ "${line}" == '<!--'* ]]; then
      continue
    fi

    if ! contains_exact_line "${line}" "${allowed_lines[@]}"; then
      echo "Unexpected non-placeholder content in ${doc_path}: ${line}" >&2
      exit 1
    fi
  done < "${doc_path}"

  local phrase
  for phrase in "${doc_required_phrases[@]}"; do
    if ! grep -Fq "${phrase}" "${doc_path}"; then
      echo "Missing placeholder statement in ${doc_path}: ${phrase}" >&2
      exit 1
    fi
  done

  if grep -Eiq "${secret_pattern}" "${doc_path}"; then
    echo "Potential active environment or secret material detected in ${doc_path}" >&2
    exit 1
  fi
}

validate_placeholder_config() {
  local category="$1"
  local config_path="$2"
  local category_description

  category_description="$(config_category_description "${category}")"

  local -a allowed_lines=(
    "schema_version: 1"
    "category: ${category}"
    "status: placeholder"
    "non_secret: true"
    "environment: template"
    "description: ${category_description}"
    "values: {}"
  )

  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ -z "${line}" ]]; then
      continue
    fi

    if [[ "${line}" == '#'* ]]; then
      continue
    fi

    if ! contains_exact_line "${line}" "${allowed_lines[@]}"; then
      echo "Unexpected non-placeholder content in ${config_path}: ${line}" >&2
      exit 1
    fi
  done < "${config_path}"

  if ! grep -Fxq "category: ${category}" "${config_path}"; then
    echo "Missing category marker in ${config_path}" >&2
    exit 1
  fi

  local phrase
  for phrase in "${config_required_phrases[@]}"; do
    if ! grep -Fq "${phrase}" "${config_path}"; then
      echo "Missing placeholder field in ${config_path}: ${phrase}" >&2
      exit 1
    fi
  done

  if grep -Eiq "${secret_pattern}" "${config_path}"; then
    echo "Potential active environment or secret material detected in ${config_path}" >&2
    exit 1
  fi
}

if [[ ! -d "${docs_dir}" ]]; then
  echo "Missing parameter docs directory: ${docs_dir}" >&2
  exit 1
fi

if [[ ! -d "${config_dir}" ]]; then
  echo "Missing parameter config directory: ${config_dir}" >&2
  exit 1
fi

expected_doc_files=("environment-parameter-catalog-structure.md")
expected_config_files=()

for category in "${approved_categories[@]}"; do
  expected_doc_files+=("${category}-parameters.md")
  expected_config_files+=("${category}.yaml")
done

assert_exact_file_set "${docs_dir}" "parameter document" "${expected_doc_files[@]}"
assert_exact_file_set "${config_dir}" "parameter config" "${expected_config_files[@]}"

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

  validate_placeholder_doc "${category}" "${doc_path}"
  validate_placeholder_config "${category}" "${config_path}"
done

for env_path in "${docs_dir}"/.env* "${config_dir}"/.env*; do
  if [[ -f "${env_path}" ]]; then
    echo "Active .env file detected in parameter catalog locations" >&2
    exit 1
  fi
done

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
