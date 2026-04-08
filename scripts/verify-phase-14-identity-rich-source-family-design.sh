#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
design_doc="${repo_root}/docs/phase-14-identity-rich-source-family-design.md"
validation_doc="${repo_root}/docs/phase-14-identity-rich-source-family-validation.md"

required_design_headings=(
  "# AegisOps Phase 14 Identity-Rich Source Family Design"
  "## 1. Purpose"
  "## 2. Approved Phase 14 Source Families and Onboarding Order"
  "## 3. Why Identity-Rich Families Are Preferred in This Phase"
  "## 4. Source-Profile and Signal-Profile Boundaries"
  "## 5. Explicit Non-Goals"
  "## 6. Baseline Alignment Notes"
)

required_design_phrases=(
  "This document defines the approved identity-rich source families for Phase 14 after the Wazuh pivot."
  "The approved Phase 14 source families are GitHub audit, Microsoft 365 audit, and Entra ID."
  "The onboarding priority is GitHub audit first, Entra ID second, and Microsoft 365 audit third."
  "Identity-rich families are preferred over broad generic source expansion in this phase because they preserve actor, target, privilege, and provenance context."
  "Wazuh remains the reviewed ingestion and normalization path for the approved Phase 14 source families."
  "No direct vendor-local actioning, generic network-wide coverage, or commercial-SIEM-style breadth is approved in Phase 14."
  'This design must remain aligned with `docs/source-onboarding-contract.md` and `docs/asset-identity-privilege-context-baseline.md`.'
)

if [[ ! -f "${design_doc}" ]]; then
  echo "Missing Phase 14 identity-rich source family design document: ${design_doc}" >&2
  exit 1
fi

for heading in "${required_design_headings[@]}"; do
  if ! grep -Fq "${heading}" "${design_doc}"; then
    echo "Missing Phase 14 design heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_design_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${design_doc}"; then
    echo "Missing Phase 14 design statement: ${phrase}" >&2
    exit 1
  fi
done

required_family_lines=(
  "### 4.1 GitHub audit"
  "### 4.2 Entra ID"
  "### 4.3 Microsoft 365 audit"
)

for family_line in "${required_family_lines[@]}"; do
  if ! grep -Fq -- "${family_line}" "${design_doc}"; then
    echo "Missing Phase 14 approved family row: ${family_line}" >&2
    exit 1
  fi
done

if [[ ! -f "${validation_doc}" ]]; then
  echo "Missing Phase 14 identity-rich source family validation record: ${validation_doc}" >&2
  exit 1
fi

required_validation_phrases=(
  "# Phase 14 Identity-Rich Source Family Validation"
  "- Validation date: 2026-04-08"
  "- Validation scope: Phase 14 review of the approved identity-rich source families, onboarding priority, source-profile boundaries, and Wazuh-backed ingestion assumptions"
  '- Baseline references: `docs/source-onboarding-contract.md`, `docs/asset-identity-privilege-context-baseline.md`, `docs/wazuh-alert-ingest-contract.md`, `docs/architecture.md`, `docs/phase-14-identity-rich-source-family-design.md`'
  '- Verification commands: `bash scripts/verify-phase-14-identity-rich-source-family-design.sh`'
  "- Validation status: PASS"
  "## Required Design-Set Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  "Confirmed the approved Phase 14 source families are ordered to maximize identity, actor, target, privilege, and provenance richness before broader source expansion is reconsidered."
  "Confirmed the reviewed source-profile boundaries keep GitHub audit, Microsoft 365 audit, and Entra ID constrained to admitted family semantics rather than vendor-local actioning or generic network-wide coverage."
  "Confirmed the Wazuh-backed ingestion path remains the reviewed intake boundary and does not authorize direct vendor-local actioning or commercial-SIEM-style breadth."
  'The design document must remain cross-linked from the source onboarding contract, the asset and identity privilege baseline, and the Wazuh alert ingest contract so the approved family boundary stays reviewable from each dependent artifact.'
  "No deviations found."
)

for phrase in "${required_validation_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${validation_doc}"; then
    echo "Missing Phase 14 validation statement in ${validation_doc}: ${phrase}" >&2
    exit 1
  fi
done

required_validation_artifacts=(
  "docs/source-onboarding-contract.md"
  "docs/asset-identity-privilege-context-baseline.md"
  "docs/wazuh-alert-ingest-contract.md"
  "docs/architecture.md"
  "docs/phase-14-identity-rich-source-family-design.md"
)

for artifact in "${required_validation_artifacts[@]}"; do
  if [[ ! -f "${repo_root}/${artifact}" ]]; then
    echo "Missing required Phase 14 design artifact: ${repo_root}/${artifact}" >&2
    exit 1
  fi

    if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}"; then
    echo "Phase 14 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Phase 14 identity-rich source family design and validation records remain reviewable and fail closed."
