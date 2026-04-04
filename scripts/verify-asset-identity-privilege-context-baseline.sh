#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/asset-identity-privilege-context-baseline.md"

required_headings=(
  "# AegisOps Asset, Identity, and Privilege Context Baseline"
  "## 1. Purpose"
  "## 2. First-Class Context Terms"
  "## 3. Minimal Resolution and Alias Claims"
  "## 4. Ownership, Criticality, and Privilege Context Expectations"
  "## 5. Hunt and Triage Usage Boundaries"
  "## 6. Explicit Non-Goals"
  "## 7. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the minimum asset, identity, and privilege context baseline for Phase 7 AI-assisted threat hunting design work."
  "This document defines baseline terms, ownership expectations, and bounded reasoning claims only. It does not approve live CMDB integration, IdP integration, or production privilege synchronization."
  '| `Asset` | A host, workload, device, application instance, or other operational computing target that may produce telemetry, receive actions, or require ownership context. |'
  '| `Identity` | A human or machine principal that may authenticate, own activity, approve work, or operate automation relevant to hunt and triage context. |'
  '| `Group` | A named collection of identities used for access assignment, administrative delegation, or scoping of privilege-relevant relationships. |'
  '| `Service Account` | A non-human identity used by automation, integrations, monitors, or workflows rather than by an interactive person. |'
  '| `Alias` | A reviewed alternate identifier that may refer to the same asset, identity, or group without asserting hidden authority beyond the mapped context. |'
  '| `Ownership` | The accountable team or role expected to know why the asset or identity exists, what it supports, and who may authorize changes. |'
  '| `Criticality` | A bounded rating that explains how operationally or security-significant an asset, identity, or group is for triage and escalation decisions. |'
  '| `Privilege Context` | The reviewed description of why an identity, group, or asset is security-sensitive because of administrative capability, delegated authority, or access to high-impact systems. |'
  "AegisOps may claim direct equality only when two records share the same stable identifier inside the same reviewed source boundary."
  "AegisOps may claim probable alias linkage only when the relationship is explicitly supplied by reviewed documentation, curated mapping, or analyst-confirmed case context."
  "AegisOps must not invent transitive identity, host, or group resolution from naming similarity alone."
  "When resolution is incomplete, the baseline expectation is to preserve the ambiguity explicitly rather than fabricate a single authoritative entity."
  "Each tracked asset should have a named owning team or role, a stated operational purpose, and a criticality expectation when that context is available."
  "Each tracked identity or service account should have a named owner, expected usage boundary, and whether the identity is interactive, shared, or automation-bound."
  "Privilege-relevant groups must be treated as context-bearing entities even when live group membership synchronization is out of scope."
  "Service accounts must remain distinct from human identities in hunt reasoning even if their names resemble individual user identifiers."
  "Host ownership, business purpose, service-account ownership, group sensitivity, and criticality may inform hunt prioritization and triage explanation, but they do not prove maliciousness by themselves."
  "Phase 7 hunt workflows may use this baseline to explain why a host, user, service account, or group deserves additional scrutiny without claiming that AegisOps already has live enterprise authority over those records."
  "This baseline permits bounded statements such as known owner, declared criticality, reviewed alias, and privilege-relevant group membership only when those statements come from approved internal reference data or analyst-reviewed case context."
  "This baseline does not make CMDB data authoritative for all asset truth, does not make an IdP authoritative for every entitlement edge, and does not authorize production entitlement automation."
  "Live CMDB integration is out of scope."
  "IdP integration for live identity or group synchronization is out of scope."
  "Production privilege sync, entitlement reconciliation, and automatic authorization changes are out of scope."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing asset, identity, and privilege context baseline document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing asset/identity/privilege baseline heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing asset/identity/privilege baseline statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Asset, identity, and privilege context baseline document is present and defines the required Phase 7 reasoning boundaries."
