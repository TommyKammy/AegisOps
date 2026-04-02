#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
curated_dir="${repo_root}/sigma/curated"
readme_path="${curated_dir}/README.md"

required_markers=(
  "Purpose: reviewed Sigma rules approved for AegisOps onboarding."
  "Status: placeholder only; no active Sigma detection rules are committed here yet."
  "Rule onboarding requires future review and explicit approval before any real rule content is added."
)

if [[ ! -d "${curated_dir}" ]]; then
  echo "Missing sigma curated directory: ${curated_dir}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing sigma curated placeholder marker: ${readme_path}" >&2
  exit 1
fi

for marker in "${required_markers[@]}"; do
  if ! grep -Fq "${marker}" "${readme_path}"; then
    echo "Missing required sigma curated marker text: ${marker}" >&2
    exit 1
  fi
done

unexpected_entries=()
while IFS= read -r path; do
  unexpected_entries+=("${path}")
done < <(find "${curated_dir}" -mindepth 1 ! -path "${readme_path}" | LC_ALL=C sort)

if (( ${#unexpected_entries[@]} > 0 )); then
  echo "Unexpected placeholder content in ${curated_dir}; only ${readme_path} is allowed." >&2
  printf ' %s\n' "${unexpected_entries[@]}" >&2
  exit 1
fi

echo "Sigma curated skeleton markers are present and placeholder-safe."
