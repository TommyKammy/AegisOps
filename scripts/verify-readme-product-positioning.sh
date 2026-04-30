#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
readme_path="${repo_root}/README.md"

required_phrases=(
  '## Product positioning'
  'Current status: AegisOps has a strong pilot foundation, but it is still pre-GA and is not yet a self-service commercial replacement.'
  'Target status: AegisOps aims to provide an AI-agent-native SMB SOC/SIEM/SOAR operating experience above Wazuh and Shuffle.'
  'Replacement means the operating experience and authoritative record chain for daily SMB security operations, not Wazuh internals, Shuffle internals, or every SIEM/SOAR capability.'
  'The Phase 51 replacement boundary is defined by `docs/adr/0011-phase-51-1-replacement-boundary.md`.'
  'Wazuh detects, AegisOps decides, records, and reconciles, and Shuffle executes reviewed delegated routine work.'
  'AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, and release truth.'
  'AI remains advisory-only and non-authoritative; it must not approve, execute, reconcile, close cases, activate detectors, or become source truth.'
  'Forbidden overclaim: AegisOps must not be described as already GA, already self-service commercial, a replacement for every SIEM/SOAR capability, a reimplementation of Wazuh or Shuffle internals, or a broad autonomous SOC.'
)

forbidden_phrases=(
  "AegisOps is already GA"
  "AegisOps is a GA replacement"
  "AegisOps is already a self-service commercial replacement"
  "AegisOps replaces every SIEM capability"
  "AegisOps replaces every SOAR capability"
  "AegisOps is a complete SIEM/SOAR replacement"
  "AI owns workflow truth"
  "AI is authoritative"
  "Wazuh owns workflow truth"
  "Wazuh owns AegisOps workflow truth"
  "Shuffle owns workflow truth"
  "Shuffle owns AegisOps workflow truth"
  "AegisOps is a broad autonomous SOC"
)

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README document: ${readme_path}" >&2
  exit 1
fi

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${readme_path}"; then
    echo "Missing README product positioning statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${forbidden_phrases[@]}"; do
  if grep -Fq -- "${phrase}" "${readme_path}"; then
    echo "Forbidden README product positioning overclaim: ${phrase}" >&2
    exit 1
  fi
done

echo "README product positioning preserves the Phase 51 replacement boundary."
