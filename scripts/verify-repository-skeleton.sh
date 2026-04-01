#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

required_directories=(
  "config"
  "docs"
  "ingest"
  "n8n"
  "opensearch"
  "proxy"
  "scripts"
  "sigma"
)

allowed_top_level_directories=(
  ".codex-supervisor"
  "config"
  "docs"
  "ingest"
  "n8n"
  "opensearch"
  "proxy"
  "scripts"
  "sigma"
)

required_files=(
  ".env.sample"
)

allowed_top_level_control_entries=(
  ".git"
)

for directory in "${required_directories[@]}"; do
  if [[ ! -d "${repo_root}/${directory}" ]]; then
    echo "Missing required top-level directory: ${directory}/" >&2
    exit 1
  fi
done

for file_path in "${required_files[@]}"; do
  if [[ ! -f "${repo_root}/${file_path}" ]]; then
    echo "Missing required top-level file: ${file_path}" >&2
    exit 1
  fi
done

for entry in "${allowed_top_level_control_entries[@]}"; do
  if [[ ! -e "${repo_root}/${entry}" ]]; then
    echo "Missing allowed top-level control entry: ${entry}" >&2
    exit 1
  fi
done

mapfile -t actual_directories < <(
  find "${repo_root}" -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort
)
mapfile -t expected_directories < <(
  printf '%s\n' "${allowed_top_level_directories[@]}" | sort
)

if [[ "${actual_directories[*]}" != "${expected_directories[*]}" ]]; then
  echo "Top-level directories do not match the approved repository skeleton." >&2
  echo "Expected directories:" >&2
  printf '  %s\n' "${expected_directories[@]}" >&2
  echo "Actual directories:" >&2
  printf '  %s\n' "${actual_directories[@]}" >&2
  exit 1
fi

echo "Repository skeleton matches the approved top-level structure."
