#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/network-exposure-and-access-path-policy.md"

required_headings=(
  "## 1. Purpose"
  "## 2. Approved Reverse Proxy Access Model"
  "## 3. Internal Service Exposure Policy"
  "## 4. Webhook Protection Policy"
  "## 5. Administrative Access Path Policy"
  "## 6. Outbound Dependency Review Rule"
)

required_phrases=(
  "All user-facing UI access must traverse the approved reverse proxy."
  "Direct exposure of internal service ports is prohibited unless explicitly approved through ADR or equivalent architecture approval."
  "Internal services must bind only to private or otherwise approved internal interfaces."
  "Webhook endpoints must require an authentication or integrity control such as a token, signature, or equivalent approved mechanism."
  "Administrative access must use documented approved paths rather than ad-hoc direct exposure of product service ports."
  "Any new always-on outbound dependency must be documented and reviewed for both security and operational impact before adoption."
  "This document defines policy only and does not change runtime networking."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing network exposure policy document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing network exposure heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing network exposure policy statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Network exposure and access path policy document covers the required rules."
