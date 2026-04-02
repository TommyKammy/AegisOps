#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/repository-structure-baseline.md"

required_entries=(
  ".codex-supervisor/"
  ".github/"
  "LICENSE.txt"
  "README.md"
  "docs/"
  "opensearch/"
  "sigma/"
  "n8n/"
  "ingest/"
  "postgres/"
  "proxy/"
  "scripts/"
  "config/"
  ".env.sample"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing repository structure document: ${doc_path}" >&2
  exit 1
fi

escape_ere() {
  printf '%s' "$1" | sed -e 's/[][(){}.^$*+?|\\]/\\&/g'
}

for entry in "${required_entries[@]}"; do
  if ! grep -Fq "\`${entry}\`" "${doc_path}"; then
    echo "Missing documented entry for ${entry}" >&2
    exit 1
  fi

  escaped_entry="$(escape_ere "${entry}")"
  if ! grep -Eq "^\\| \`${escaped_entry}\` \\| .*[[:alnum:]].*\\|$" "${doc_path}"; then
    echo "Missing purpose description for ${entry}" >&2
    exit 1
  fi
done

echo "Repository structure baseline document is present and covers all required entries."
