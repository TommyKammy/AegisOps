#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/storage-layout-and-mount-policy.md"

required_headings=(
  "## 1. Purpose"
  "## 2. Mount Point Naming Policy"
  "## 3. Persistent Storage Layout"
  "### 3.1 OpenSearch"
  "### 3.2 PostgreSQL"
  "### 3.3 n8n"
  "## 4. Backup Separation Policy"
  "## 5. VM Snapshot Limitation"
)

required_examples=(
  "/srv/aegisops/opensearch-data"
  "/srv/aegisops/postgres-data"
  "/srv/aegisops/n8n-data"
  "/srv/aegisops-backup"
)

required_phrases=(
  "OpenSearch persistent data must be mounted only from a dedicated host path."
  "PostgreSQL persistent data must be mounted only from a dedicated host path."
  "n8n persistent state must be mounted only from a dedicated host path."
  "Backup storage must not share the same filesystem mount as primary runtime data."
  "Hypervisor VM snapshots are not an application-aware backup for OpenSearch or PostgreSQL."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing storage policy document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing storage policy heading: ${heading}" >&2
    exit 1
  fi
done

for example in "${required_examples[@]}"; do
  if ! grep -Fq "${example}" "${doc_path}"; then
    echo "Missing storage path example: ${example}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing storage policy statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Storage layout and mount policy document covers the required rules."
