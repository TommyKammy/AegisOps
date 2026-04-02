#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
workflow_root="${repo_root}/n8n/workflows"

expected_categories=(
  "aegisops_alert_ingest"
  "aegisops_approve"
  "aegisops_enrich"
  "aegisops_notify"
  "aegisops_response"
)

if [[ ! -d "${workflow_root}" ]]; then
  echo "Missing n8n workflow skeleton directory: ${workflow_root}" >&2
  exit 1
fi

actual_categories=()
while IFS= read -r category; do
  actual_categories+=("${category}")
done < <(
  find "${workflow_root}" -mindepth 1 -maxdepth 1 -type d \
    | sed 's#.*/##' \
    | LC_ALL=C sort
)

expected_sorted=()
while IFS= read -r category; do
  expected_sorted+=("${category}")
done < <(
  printf '%s\n' "${expected_categories[@]}" | LC_ALL=C sort
)

for category in "${expected_categories[@]}"; do
  category_path="${workflow_root}/${category}"

  if [[ ! -d "${category_path}" ]]; then
    echo "Missing n8n workflow category placeholder: ${category_path}" >&2
    exit 1
  fi

  if [[ ! -f "${category_path}/.gitkeep" ]]; then
    echo "Missing placeholder file for n8n workflow category: ${category_path}/.gitkeep" >&2
    exit 1
  fi

  unexpected_files=()
  while IFS= read -r path; do
    unexpected_files+=("${path}")
  done < <(
    find "${category_path}" -mindepth 1 -type f ! -name '.gitkeep' | LC_ALL=C sort
  )

  if ((${#unexpected_files[@]} > 0)); then
    echo "n8n workflow category placeholders must not introduce workflow logic: ${category_path}" >&2
    printf 'Unexpected files:\n' >&2
    printf '  %s\n' "${unexpected_files[@]}" >&2
    exit 1
  fi
done

if [[ "${actual_categories[*]}" != "${expected_sorted[*]}" ]]; then
  echo "Tracked n8n workflow categories do not match the approved placeholder skeleton." >&2
  echo "Expected categories:" >&2
  printf '  %s\n' "${expected_sorted[@]}" >&2
  echo "Actual categories:" >&2
  printf '  %s\n' "${actual_categories[@]}" >&2
  exit 1
fi

echo "n8n workflow category skeleton matches the approved placeholder-safe structure."
