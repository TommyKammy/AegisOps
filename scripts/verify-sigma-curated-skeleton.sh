#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
curated_dir="${repo_root}/sigma/curated"
readme_path="${curated_dir}/README.md"
windows_dir="${curated_dir}/windows-security-and-endpoint"

expected_entries=(
  "${readme_path}"
  "${windows_dir}/audit-log-cleared.yml"
  "${windows_dir}/new-local-user-created.yml"
  "${windows_dir}/privileged-group-membership-change.yml"
)

verify_required_file() {
  local file_path="$1"
  local missing_label="$2"
  local regular_file_label="$3"

  if [[ -L "${file_path}" ]]; then
    echo "${regular_file_label} must be a regular file: ${file_path}" >&2
    exit 1
  fi

  if [[ ! -f "${file_path}" ]]; then
    echo "Missing ${missing_label}: ${file_path}" >&2
    exit 1
  fi
}

require_phrase() {
  local file_path="$1"
  local phrase="$2"

  if ! grep -Fq -- "${phrase}" "${file_path}"; then
    echo "Curated Sigma content is missing required reviewed field: ${file_path}: ${phrase}" >&2
    exit 1
  fi
}

forbid_phrase() {
  local file_path="$1"
  local phrase="$2"

  if grep -Fq -- "${phrase}" "${file_path}"; then
    echo "Curated Sigma content still uses forbidden reviewed field: ${file_path}: ${phrase}" >&2
    exit 1
  fi
}

if [[ ! -d "${curated_dir}" ]]; then
  echo "Missing sigma curated directory: ${curated_dir}" >&2
  exit 1
fi

verify_required_file \
  "${readme_path}" \
  "curated Sigma README" \
  "Curated Sigma README"

verify_required_file \
  "${windows_dir}/privileged-group-membership-change.yml" \
  "curated Sigma rule" \
  "Curated Sigma rule"

verify_required_file \
  "${windows_dir}/audit-log-cleared.yml" \
  "curated Sigma rule" \
  "Curated Sigma rule"

verify_required_file \
  "${windows_dir}/new-local-user-created.yml" \
  "curated Sigma rule" \
  "Curated Sigma rule"

for reviewed_rule in \
  "${windows_dir}/privileged-group-membership-change.yml" \
  "${windows_dir}/audit-log-cleared.yml" \
  "${windows_dir}/new-local-user-created.yml"; do
  require_phrase "${reviewed_rule}" "field_semantics:"
  require_phrase "${reviewed_rule}" "match_required:"
  require_phrase "${reviewed_rule}" "triage_required:"
  require_phrase "${reviewed_rule}" "activation_gating:"
  require_phrase "${reviewed_rule}" "confidence_degrading:"
  require_phrase "${reviewed_rule}" "schema-reviewed"
  require_phrase "${reviewed_rule}" "detection-ready"
  forbid_phrase "${reviewed_rule}" "field_dependencies:"
done

unexpected_entries=()
symlink_entries=()
while IFS= read -r path; do
  if [[ -L "${path}" ]]; then
    symlink_entries+=("${path}")
    continue
  fi

  match_found=0
  for expected in "${expected_entries[@]}"; do
    if [[ "${path}" == "${expected}" ]]; then
      match_found=1
      break
    fi
  done

  if [[ "${match_found}" -eq 0 ]]; then
    unexpected_entries+=("${path}")
  fi
done < <(find "${curated_dir}" \( -type f -o -type l \) | LC_ALL=C sort)

if (( ${#symlink_entries[@]} > 0 )); then
  echo "Curated Sigma content must not include symlinks." >&2
  printf ' %s\n' "${symlink_entries[@]}" >&2
  exit 1
fi

if (( ${#unexpected_entries[@]} > 0 )); then
  echo "Unexpected curated Sigma content outside the selected Phase 6 slice." >&2
  printf ' %s\n' "${unexpected_entries[@]}" >&2
  exit 1
fi

echo "Curated Sigma rules and metadata are present for the selected Windows Phase 6 use cases."
