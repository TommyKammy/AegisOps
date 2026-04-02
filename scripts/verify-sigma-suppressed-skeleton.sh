#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
suppressed_dir="${repo_root}/sigma/suppressed"
readme_path="${suppressed_dir}/README.md"

required_markers=(
  "Purpose: approved home for future Sigma suppression decisions that have been reviewed and documented."
  "Status: placeholder only; no active Sigma suppression rules, exceptions, or decisions are committed here yet."
  "Any future suppression entry must include documented justification, review, and approval before real content is added."
)

if [[ ! -d "${suppressed_dir}" ]]; then
  echo "Missing sigma suppressed directory: ${suppressed_dir}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing sigma suppressed placeholder marker: ${readme_path}" >&2
  exit 1
fi

for marker in "${required_markers[@]}"; do
  if ! grep -Fq "${marker}" "${readme_path}"; then
    echo "Missing required sigma suppressed marker text: ${marker}" >&2
    exit 1
  fi
done

unexpected_entries=()
while IFS= read -r path; do
  unexpected_entries+=("${path}")
done < <(find "${suppressed_dir}" -mindepth 1 ! -path "${readme_path}" | LC_ALL=C sort)

if (( ${#unexpected_entries[@]} > 0 )); then
  echo "Unexpected placeholder content in ${suppressed_dir}; only ${readme_path} is allowed." >&2
  printf ' %s\n' "${unexpected_entries[@]}" >&2
  exit 1
fi

echo "Sigma suppressed skeleton markers are present and placeholder-safe."
