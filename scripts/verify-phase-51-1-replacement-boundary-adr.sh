#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0011-phase-51-1-replacement-boundary.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# ADR-0011: Phase 51.1 SMB SecOps Replacement Boundary"
  "## 1. Context"
  "## 2. Decision"
  "## 3. Allowed Replacement Claims"
  "## 4. Disallowed Replacement Claims"
  "## 5. Authority Boundary"
  "## 6. Substrate Responsibilities"
  "## 7. Implementation Impact"
  "## 8. Security Impact"
  "## 9. Rollback / Exit Strategy"
  "## 10. Validation"
  "## 11. Non-Goals"
  "## 12. Approval"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-04-30"
  "- **Related Issues**: #1041, #1042"
  "AegisOps replaces the SMB SecOps operating experience, not Wazuh internals, Shuffle internals, or every SIEM and SOAR capability."
  "Replacement means the reviewed operator experience for daily SMB SOC work: Wazuh detects, AegisOps decides, records, and reconciles, and Shuffle executes reviewed delegated routine work."
  "Wazuh is the detection substrate."
  "Shuffle is the routine automation substrate."
  "Allowed claim: AegisOps can replace the daily SMB SOC operating experience above Wazuh and Shuffle."
  "Allowed claim: AegisOps can replace ad hoc ticket-and-script coordination with authoritative alert, case, approval, action request, receipt, reconciliation, audit, and release records."
  "Allowed claim: AegisOps can provide a governed SIEM/SOAR operating layer for SMB teams when Wazuh and Shuffle provide the reviewed substrate capabilities."
  "Disallowed claim: AegisOps already replaces every SIEM capability."
  "Disallowed claim: AegisOps already replaces every SOAR capability."
  "Disallowed claim: AegisOps reimplements Wazuh detection internals."
  "Disallowed claim: AegisOps reimplements Shuffle workflow internals."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, and release truth."
  "AI must not approve actions, execute actions, reconcile execution, close cases, activate detectors, or become source truth."
  "Wazuh alert status is not AegisOps case truth."
  "Shuffle workflow success is not AegisOps reconciliation truth."
  "Tickets, evidence systems, browser state, UI cache, downstream receipts, demo data, Wazuh, Shuffle, and AI output remain subordinate context."
  "This ADR rejects any shortcut that promotes subordinate surfaces into AegisOps workflow truth."
  "This ADR does not implement CLI behavior, Wazuh profile generation, Shuffle profile generation, AI daily operations, SIEM breadth, SOAR breadth, packaging, release-candidate behavior, or general-availability behavior."
  "Run \`bash scripts/verify-phase-51-1-replacement-boundary-adr.sh\`."
  "Run \`bash scripts/test-verify-phase-51-1-replacement-boundary-adr.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1042 --config <supervisor-config-path>\`."
)

forbidden_phrases=(
  "Allowed claim: AegisOps already replaces every SIEM capability"
  "Allowed claim: AegisOps already replaces every SOAR capability"
  "AegisOps is a complete replacement for every SIEM capability"
  "AegisOps is a complete replacement for every SOAR capability"
  "AI may approve actions"
  "AI may execute actions"
  "AI may reconcile execution"
  "AI may close cases"
  "AI may activate detectors"
  "AI may become source truth"
  "Wazuh alert status is AegisOps case truth"
  "Shuffle workflow success is AegisOps reconciliation truth"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 51.1 replacement boundary ADR: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 51.1 replacement boundary ADR heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 51.1 replacement boundary ADR statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${forbidden_phrases[@]}"; do
  if grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Forbidden Phase 51.1 replacement boundary ADR claim: ${phrase}" >&2
    exit 1
  fi
done

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 51.1 ADR link check: ${readme_path}" >&2
  exit 1
fi

if ! grep -Fq -- "docs/adr/0011-phase-51-1-replacement-boundary.md" "${readme_path}"; then
  echo "README must link the Phase 51.1 replacement boundary ADR." >&2
  exit 1
fi

echo "Phase 51.1 replacement boundary ADR is present and fixes replacement claims, substrate roles, authority boundaries, and validation commands."
