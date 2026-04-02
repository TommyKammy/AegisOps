#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
doc_path="${repo_root}/docs/compose-skeleton-overview.md"

required_headings=(
  "## 1. Purpose"
  "## 2. What The Skeletons Are For"
  "## 3. What Remains Out of Scope"
  "## 4. Contributor Guidance"
  "## 5. Reference Documents"
)

required_phrases=(
  "The compose skeletons exist to provide placeholder-safe scaffolding for approved AegisOps component boundaries."
  "They are not production-ready deployment definitions."
  "They do not introduce new architecture, deployment behavior, or runtime defaults."
  "Treat the skeletons as contributor scaffolding, not as a complete deployment design."
  "Do not treat placeholder paths, placeholder environment values, or placeholder profiles as approved production settings."
)

required_references=(
  '`docs/requirements-baseline.md`'
  '`docs/contributor-naming-guide.md`'
  '`docs/network-exposure-and-access-path-policy.md`'
  '`docs/storage-layout-and-mount-policy.md`'
  '`docs/repository-structure-baseline.md`'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing compose skeleton overview document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing compose skeleton overview heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing compose skeleton overview statement: ${phrase}" >&2
    exit 1
  fi
done

for reference in "${required_references[@]}"; do
  if ! grep -Fq "${reference}" "${doc_path}"; then
    echo "Missing compose skeleton overview reference: ${reference}" >&2
    exit 1
  fi
done

echo "Compose skeleton overview document covers the required boundaries and references."
