#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/requirements-baseline.md"

required_headings=(
  "### 7.1 Product Naming"
  "### 7.2 Hostname Naming"
  "### 7.3 Docker Compose Project Naming"
  "### 7.4 OpenSearch Index Naming"
  "### 7.5 Detector Naming"
  "### 7.6 n8n Workflow Naming"
  "### 7.7 Secret and Environment Variable Naming"
)

required_examples=(
  "aegisops-opensearch-node-01"
  "aegisops-opensearch"
  "aegisops-logs-windows-*"
  "aegisops-windows-suspicious-powershell-high"
  "aegisops_enrich_*"
  "AEGISOPS_OPENSEARCH_ADMIN_PASSWORD"
)

legacy_names=(
  "wazuh"
  "elastic"
  "elk"
  "securityonion"
  "security onion"
  "splunk"
  "sentinel"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing requirements baseline document: ${doc_path}" >&2
  exit 1
fi

section_text="$(
  awk '
    /^## 7\. Naming Conventions$/ { in_section=1 }
    /^## / && in_section && !/^## 7\. Naming Conventions$/ { exit }
    in_section { print }
  ' "${doc_path}"
)"

if [[ -z "${section_text}" ]]; then
  echo "Missing naming conventions section in ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" <<<"${section_text}"; then
    echo "Missing naming heading: ${heading}" >&2
    exit 1
  fi
done

for example in "${required_examples[@]}"; do
  if ! grep -Fq "${example}" <<<"${section_text}"; then
    echo "Missing naming example: ${example}" >&2
    exit 1
  fi
done

for legacy_name in "${legacy_names[@]}"; do
  if grep -Eiq "(^|[^[:alnum:]])${legacy_name}([^[:alnum:]]|$)" <<<"${section_text}"; then
    echo "Legacy product naming found in naming conventions section: ${legacy_name}" >&2
    exit 1
  fi
done

echo "Naming conventions section covers the required categories and examples."
