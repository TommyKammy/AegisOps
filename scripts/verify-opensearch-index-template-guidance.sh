#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
doc_path="${repo_root}/opensearch/index-templates/README.md"

required_headings=(
  "## 1. Purpose"
  "## 2. Placeholder Scope"
  "## 3. What Remains Out of Scope"
  "## 4. Contributor Guidance"
  "## 5. Reference Documents"
)

required_phrases=(
  "These files exist to reserve the approved OpenSearch log index-template names and directory ownership for AegisOps contributors."
  "They are placeholders only and are not production-ready index templates."
  "Do not treat the current files as approved mappings, settings, shard plans, lifecycle policies, or ingestion contracts."
  "Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline."
)

required_references=(
  '`docs/requirements-baseline.md`'
  '`docs/contributor-naming-guide.md`'
  '`docs/repository-structure-baseline.md`'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing OpenSearch index template guidance document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing OpenSearch index template guidance heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing OpenSearch index template guidance statement: ${phrase}" >&2
    exit 1
  fi
done

for reference in "${required_references[@]}"; do
  if ! grep -Fq "${reference}" "${doc_path}"; then
    echo "Missing OpenSearch index template guidance reference: ${reference}" >&2
    exit 1
  fi
done

echo "OpenSearch index template guidance documents placeholder intent, limits, and baseline references."
