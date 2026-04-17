#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

expected_top_level_entries=(
  ".codex-supervisor"
  ".env.sample"
  ".github"
  ".gitignore"
  "LICENSE.txt"
  "README.md"
  "config"
  "control-plane"
  "docs"
  "ingest"
  "n8n"
  "opensearch"
  "postgres"
  "proxy"
  "scripts"
  "sigma"
)

if ! git -C "${repo_root}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a Git working tree: ${repo_root}" >&2
  exit 1
fi

actual_tracked_entries=()
while IFS= read -r entry; do
  actual_tracked_entries+=("${entry}")
done < <(
  git -C "${repo_root}" ls-files \
    | awk -F/ '{print $1}' \
    | LC_ALL=C sort -u
)

expected_entries=()
while IFS= read -r entry; do
  expected_entries+=("${entry}")
done < <(
  printf '%s\n' "${expected_top_level_entries[@]}" | LC_ALL=C sort
)

for entry in "${expected_top_level_entries[@]}"; do
  if ! printf '%s\n' "${actual_tracked_entries[@]}" | grep -Fx "${entry}" >/dev/null; then
    echo "Missing required tracked top-level entry: ${entry}" >&2
    exit 1
  fi
done

if [[ "${actual_tracked_entries[*]}" != "${expected_entries[*]}" ]]; then
  echo "Tracked top-level entries do not match the approved repository skeleton." >&2
  echo "Expected tracked entries:" >&2
  printf '  %s\n' "${expected_entries[@]}" >&2
  echo "Actual tracked entries:" >&2
  printf '  %s\n' "${actual_tracked_entries[@]}" >&2
  exit 1
fi

disallowed_supervisor_paths=(
  ".codex-supervisor/issues/*/issue-journal.md"
  ".codex-supervisor/execution-metrics/*"
  ".codex-supervisor/pre-merge/*"
  ".codex-supervisor/replay/*"
  ".codex-supervisor/turn-in-progress.json"
)

for pattern in "${disallowed_supervisor_paths[@]}"; do
  while IFS= read -r tracked_path; do
    [[ -n "${tracked_path}" ]] || continue
    echo "Tracked supervisor-local journal is not allowed: ${tracked_path}" >&2
    exit 1
  done < <(git -C "${repo_root}" ls-files "${pattern}")
done

echo "Repository skeleton matches the approved tracked top-level structure."
