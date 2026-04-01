#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/contributor-naming-guide.md"

required_headings=(
  "## Purpose"
  "## Baseline Source"
  "## Naming Rules"
  "### Hosts"
  "### Compose Projects"
  "### OpenSearch Indexes"
  "### Detectors"
  "### n8n Workflows"
  "### Environment Variables and Secrets"
)

required_examples=(
  "aegisops-opensearch-node-01"
  "aegisops-n8n-node"
  "aegisops-opensearch"
  "aegisops-logs-windows-*"
  "aegisops-findings-*"
  "aegisops-windows-suspicious-powershell-high"
  "aegisops_enrich_ip_reputation"
  "AEGISOPS_OPENSEARCH_ADMIN_PASSWORD"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing contributor naming guide: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing heading in contributor naming guide: ${heading}" >&2
    exit 1
  fi
done

for example in "${required_examples[@]}"; do
  if ! grep -Fq "${example}" "${doc_path}"; then
    echo "Missing example in contributor naming guide: ${example}" >&2
    exit 1
  fi
done

if ! grep -Fq "docs/requirements-baseline.md" "${doc_path}"; then
  echo "Contributor naming guide must cite docs/requirements-baseline.md as the source of truth." >&2
  exit 1
fi

if rg -n '\b(wazuh|elastic|elk|securityonion|security onion|splunk|sentinel)\b' "${doc_path}" >/dev/null; then
  echo "Contributor naming guide contains legacy product naming." >&2
  exit 1
fi

echo "Contributor naming guide is present and covers the required naming categories."
