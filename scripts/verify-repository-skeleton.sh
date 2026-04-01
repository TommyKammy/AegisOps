#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

expected_top_level_entries=(
  ".env.sample"
  "config"
  "docs"
  "ingest"
  "n8n"
  "opensearch"
  "proxy"
  "scripts"
  "sigma"
)

for entry in "${expected_top_level_entries[@]}"; do
  if [[ ! -e "${repo_root}/${entry}" ]]; then
    echo "Missing required top-level entry: ${entry}" >&2
    exit 1
  fi
done

if [[ ! -e "${repo_root}/.git" ]]; then
  echo "Missing repository control entry: .git" >&2
  exit 1
fi

mapfile -t actual_tracked_entries < <(
  git -C "${repo_root}" ls-tree --name-only HEAD | LC_ALL=C sort
)
mapfile -t expected_entries < <(
  printf '%s\n' "${expected_top_level_entries[@]}" | LC_ALL=C sort
)

if [[ "${actual_tracked_entries[*]}" != "${expected_entries[*]}" ]]; then
  echo "Tracked top-level entries do not match the approved repository skeleton." >&2
  echo "Expected tracked entries:" >&2
  printf '  %s\n' "${expected_entries[@]}" >&2
  echo "Actual tracked entries:" >&2
  printf '  %s\n' "${actual_tracked_entries[@]}" >&2
  exit 1
fi

echo "Repository skeleton matches the approved tracked top-level structure."
