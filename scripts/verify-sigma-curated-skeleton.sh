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

file_sha256() {
  local file_path="$1"

  shasum -a 256 "${file_path}" | awk '{print $1}'
}

verify_exact_file() {
  local file_path="$1"
  local missing_label="$2"
  local regular_file_label="$3"
  local expected_hash="$4"
  local actual_hash

  if [[ -L "${file_path}" ]]; then
    echo "${regular_file_label} must be a regular file: ${file_path}" >&2
    exit 1
  fi

  if [[ ! -f "${file_path}" ]]; then
    echo "Missing ${missing_label}: ${file_path}" >&2
    exit 1
  fi

  actual_hash="$(file_sha256 "${file_path}")"
  if [[ "${actual_hash}" != "${expected_hash}" ]]; then
    echo "Curated Sigma content does not match reviewed baseline: ${file_path}" >&2
    exit 1
  fi
}

if [[ ! -d "${curated_dir}" ]]; then
  echo "Missing sigma curated directory: ${curated_dir}" >&2
  exit 1
fi

verify_exact_file \
  "${readme_path}" \
  "curated Sigma README" \
  "Curated Sigma README" \
  "c09c0ab87f89cef5c4c8bdd61ea4b4d06694fea254a6687aab9d27992aa527a8"

verify_exact_file \
  "${windows_dir}/privileged-group-membership-change.yml" \
  "curated Sigma rule" \
  "Curated Sigma rule" \
  "ab631659730f723660f9543473e31cbd5d61dfa1454ab2410301686d0d4ee7dc"

verify_exact_file \
  "${windows_dir}/audit-log-cleared.yml" \
  "curated Sigma rule" \
  "Curated Sigma rule" \
  "17a1daa0558e2e80f012cd7de70664c062d6e52f6bfb55054b5c669b14308d3d"

verify_exact_file \
  "${windows_dir}/new-local-user-created.yml" \
  "curated Sigma rule" \
  "Curated Sigma rule" \
  "d9f20b6ac5f20eae0001bbd5189bbbedaea1a073574da4efc69723b442ce944f"

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
