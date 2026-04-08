#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-14-identity-rich-source-family-design.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_support_docs() {
  local target="$1"

  cat <<'EOF' >"${target}/docs/source-onboarding-contract.md"
# AegisOps Source Onboarding Contract
EOF
  cat <<'EOF' >"${target}/docs/asset-identity-privilege-context-baseline.md"
# AegisOps Asset, Identity, and Privilege Context Baseline
EOF
  cat <<'EOF' >"${target}/docs/wazuh-alert-ingest-contract.md"
# Wazuh Alert Ingest Contract
EOF
  cat <<'EOF' >"${target}/docs/architecture.md"
# AegisOps Architecture Overview
EOF

  git -C "${target}" add docs/source-onboarding-contract.md docs/asset-identity-privilege-context-baseline.md docs/wazuh-alert-ingest-contract.md docs/architecture.md
}

write_doc() {
  local target="$1"
  local path="$2"
  local doc_content="$3"

  printf '%s\n' "${doc_content}" >"${target}/${path}"
  git -C "${target}" add "${path}"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_support_docs "${valid_repo}"
write_doc "${valid_repo}" "docs/phase-14-identity-rich-source-family-design.md" '# AegisOps Phase 14 Identity-Rich Source Family Design

## 1. Purpose

This document defines the approved identity-rich source families for Phase 14 after the Wazuh pivot.

It supplements `docs/source-onboarding-contract.md`, `docs/asset-identity-privilege-context-baseline.md`, `docs/wazuh-alert-ingest-contract.md`, and `docs/architecture.md` by narrowing the Phase 14 onboarding path to source families that preserve actor, target, privilege, and provenance context.

This document defines review scope only. It does not approve live vendor actioning, direct source-side automation, generic network-wide coverage, or commercial-SIEM-style breadth.

## 2. Approved Phase 14 Source Families and Onboarding Order

The approved Phase 14 source families are GitHub audit, Microsoft 365 audit, and Entra ID.

The onboarding priority is GitHub audit first, Entra ID second, and Microsoft 365 audit third.

This order favors the source families that most directly preserve accountable actor, target object, privilege change, and provenance detail for the AegisOps control-plane and analyst workflow.

## 3. Why Identity-Rich Families Are Preferred in This Phase

Identity-rich families are preferred over broad generic source expansion in this phase because they preserve actor, target, privilege, and provenance context.

That context is more useful for control-plane review than a broader family list with weaker source identity and privilege semantics.

The reviewed family set also keeps the onboarding problem bounded enough for Wazuh-backed normalization, replay review, and provenance preservation without reopening the thesis of broad substrate replacement.

Wazuh remains the reviewed ingestion and normalization path for the approved Phase 14 source families.

## 4. Source-Profile and Signal-Profile Boundaries

### 4.1 GitHub audit

| Aspect | Review expectation |
| ---- | ---- |
| Source identity | Organization, repository, audit-log stream, and delivery path remain explicit. |
| Actor | Human user, service account, GitHub App, or automation identity must remain attributable when present. |
| Target | Repository, branch, pull request, workflow, secret, environment, setting, or membership object remains explicit. |
| Privilege | Owner, maintainer, admin, codeowner, workflow, token, or permission-change context must remain reviewable. |
| Provenance | Audit action, request id, delivery timestamp, actor type, and object identifiers must remain preserved. |

GitHub audit signals are expected to be high-value approval-context inputs because repository and workflow changes often map directly to access, release, and approval boundaries.

### 4.2 Entra ID

| Aspect | Review expectation |
| ---- | ---- |
| Source identity | Tenant, directory, and audit category remain explicit. |
| Actor | Human user, service principal, managed identity, or administrative actor must remain attributable when present. |
| Target | User, group, role assignment, app registration, credential object, or policy object remains explicit. |
| Privilege | Admin role grant, delegated permission, group membership, consent, or credential change context must remain reviewable. |
| Provenance | Operation name, activity time, correlation id, tenant, and initiatedBy / targetResources structure must remain preserved. |

Entra ID signals are expected to provide the strongest directory and privilege context for analyst triage and approval review.

### 4.3 Microsoft 365 audit

| Aspect | Review expectation |
| ---- | ---- |
| Source identity | Tenant and workload boundary remain explicit. |
| Actor | User, admin, or service identity must remain attributable when present. |
| Target | Mailbox, site, document, team, policy, sharing link, or message object remains explicit. |
| Privilege | Administrative action, sharing change, consent, retention change, or policy update context must remain reviewable. |
| Provenance | Workload, operation, record type, actor id, target id, and event time must remain preserved. |

Microsoft 365 audit signals are expected to broaden approval-context coverage without becoming a generic platform-wide telemetry grab bag.

## 5. Explicit Non-Goals

No direct vendor-local actioning, generic network-wide coverage, or commercial-SIEM-style breadth is approved in Phase 14.

This phase does not approve live identity sync, permission reconciliation, or automatic enforcement based on these families alone.

## 6. Baseline Alignment Notes

This design must remain aligned with `docs/source-onboarding-contract.md` and `docs/asset-identity-privilege-context-baseline.md`.

It also remains aligned with `docs/wazuh-alert-ingest-contract.md` and `docs/architecture.md` by keeping Wazuh as the reviewed ingestion path and AegisOps as the authority for downstream workflow state.'
commit_fixture "${valid_repo}"
write_doc "${valid_repo}" "docs/phase-14-identity-rich-source-family-validation.md" '# Phase 14 Identity-Rich Source Family Validation

- Validation date: 2026-04-08
- Validation scope: Phase 14 review of the approved identity-rich source families, onboarding priority, source-profile boundaries, and Wazuh-backed ingestion assumptions
- Baseline references: `docs/source-onboarding-contract.md`, `docs/asset-identity-privilege-context-baseline.md`, `docs/wazuh-alert-ingest-contract.md`, `docs/architecture.md`, `docs/phase-14-identity-rich-source-family-design.md`
- Verification commands: `bash scripts/verify-phase-14-identity-rich-source-family-design.sh`
- Validation status: PASS

## Required Design-Set Artifacts

- `docs/source-onboarding-contract.md`
- `docs/asset-identity-privilege-context-baseline.md`
- `docs/wazuh-alert-ingest-contract.md`
- `docs/architecture.md`
- `docs/phase-14-identity-rich-source-family-design.md`

## Review Outcome

Confirmed the approved Phase 14 source families are ordered to maximize identity, actor, target, privilege, and provenance richness before broader source expansion is reconsidered.

Confirmed the reviewed source-profile boundaries keep GitHub audit, Microsoft 365 audit, and Entra ID constrained to admitted family semantics rather than vendor-local actioning or generic network-wide coverage.

Confirmed the Wazuh-backed ingestion path remains the reviewed intake boundary and does not authorize direct vendor-local actioning or commercial-SIEM-style breadth.

## Cross-Link Review

The design document must remain cross-linked from the source onboarding contract, the asset and identity privilege baseline, and the Wazuh alert ingest contract so the approved family boundary stays reviewable from each dependent artifact.

## Deviations

No deviations found.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Phase 14 identity-rich source family design document:"

missing_validation_repo="${workdir}/missing-validation"
create_repo "${missing_validation_repo}"
write_support_docs "${missing_validation_repo}"
write_doc "${missing_validation_repo}" "docs/phase-14-identity-rich-source-family-design.md" '# AegisOps Phase 14 Identity-Rich Source Family Design

## 1. Purpose

This document defines the approved identity-rich source families for Phase 14 after the Wazuh pivot.

It supplements `docs/source-onboarding-contract.md`, `docs/asset-identity-privilege-context-baseline.md`, `docs/wazuh-alert-ingest-contract.md`, and `docs/architecture.md` by narrowing the Phase 14 onboarding path to source families that preserve actor, target, privilege, and provenance context.

This document defines review scope only. It does not approve live vendor actioning, direct source-side automation, generic network-wide coverage, or commercial-SIEM-style breadth.

## 2. Approved Phase 14 Source Families and Onboarding Order

The approved Phase 14 source families are GitHub audit, Microsoft 365 audit, and Entra ID.

The onboarding priority is GitHub audit first, Entra ID second, and Microsoft 365 audit third.

This order favors the source families that most directly preserve accountable actor, target object, privilege change, and provenance detail for the AegisOps control-plane and analyst workflow.

## 3. Why Identity-Rich Families Are Preferred in This Phase

Identity-rich families are preferred over broad generic source expansion in this phase because they preserve actor, target, privilege, and provenance context.

That context is more useful for control-plane review than a broader family list with weaker source identity and privilege semantics.

The reviewed family set also keeps the onboarding problem bounded enough for Wazuh-backed normalization, replay review, and provenance preservation without reopening the thesis of broad substrate replacement.

Wazuh remains the reviewed ingestion and normalization path for the approved Phase 14 source families.

## 4. Source-Profile and Signal-Profile Boundaries

### 4.1 GitHub audit

| Aspect | Review expectation |
| ---- | ---- |
| Source identity | Organization, repository, audit-log stream, and delivery path remain explicit. |
| Actor | Human user, service account, GitHub App, or automation identity must remain attributable when present. |
| Target | Repository, branch, pull request, workflow, secret, environment, setting, or membership object remains explicit. |
| Privilege | Owner, maintainer, admin, codeowner, workflow, token, or permission-change context must remain reviewable. |
| Provenance | Audit action, request id, delivery timestamp, actor type, and object identifiers must remain preserved. |

GitHub audit signals are expected to be high-value approval-context inputs because repository and workflow changes often map directly to access, release, and approval boundaries.

### 4.2 Entra ID

| Aspect | Review expectation |
| ---- | ---- |
| Source identity | Tenant, directory, and audit category remain explicit. |
| Actor | Human user, service principal, managed identity, or administrative actor must remain attributable when present. |
| Target | User, group, role assignment, app registration, credential object, or policy object remains explicit. |
| Privilege | Admin role grant, delegated permission, group membership, consent, or credential change context must remain reviewable. |
| Provenance | Operation name, activity time, correlation id, tenant, and initiatedBy / targetResources structure must remain preserved. |

Entra ID signals are expected to provide the strongest directory and privilege context for analyst triage and approval review.

### 4.3 Microsoft 365 audit

| Aspect | Review expectation |
| ---- | ---- |
| Source identity | Tenant and workload boundary remain explicit. |
| Actor | User, admin, or service identity must remain attributable when present. |
| Target | Mailbox, site, document, team, policy, sharing link, or message object remains explicit. |
| Privilege | Administrative action, sharing change, consent, retention change, or policy update context must remain reviewable. |
| Provenance | Workload, operation, record type, actor id, target id, and event time must remain preserved. |

Microsoft 365 audit signals are expected to broaden approval-context coverage without becoming a generic platform-wide telemetry grab bag.

## 5. Explicit Non-Goals

No direct vendor-local actioning, generic network-wide coverage, or commercial-SIEM-style breadth is approved in Phase 14.

This phase does not approve live identity sync, permission reconciliation, or automatic enforcement based on these families alone.

## 6. Baseline Alignment Notes

This design must remain aligned with `docs/source-onboarding-contract.md` and `docs/asset-identity-privilege-context-baseline.md`.

It also remains aligned with `docs/wazuh-alert-ingest-contract.md` and `docs/architecture.md` by keeping Wazuh as the reviewed ingestion path and AegisOps as the authority for downstream workflow state.'
write_doc "${missing_validation_repo}" "docs/phase-14-identity-rich-source-family-validation.md" '# Phase 14 Identity-Rich Source Family Validation

- Validation date: 2026-04-08
- Validation scope: Phase 14 review of the approved identity-rich source families, onboarding priority, source-profile boundaries, and Wazuh-backed ingestion assumptions
- Baseline references: `docs/source-onboarding-contract.md`, `docs/asset-identity-privilege-context-baseline.md`, `docs/wazuh-alert-ingest-contract.md`, `docs/architecture.md`, `docs/phase-14-identity-rich-source-family-design.md`
- Verification commands: `bash scripts/verify-phase-14-identity-rich-source-family-design.sh`
- Validation status: PASS

## Required Design-Set Artifacts

- `docs/source-onboarding-contract.md`
- `docs/asset-identity-privilege-context-baseline.md`
- `docs/wazuh-alert-ingest-contract.md`
- `docs/architecture.md`
- `docs/phase-14-identity-rich-source-family-design.md`

## Review Outcome

Confirmed the approved Phase 14 source families are ordered to maximize identity, actor, target, privilege, and provenance richness before broader source expansion is reconsidered.

Confirmed the reviewed source-profile boundaries keep GitHub audit, Microsoft 365 audit, and Entra ID constrained to admitted family semantics rather than vendor-local actioning or generic network-wide coverage.

Confirmed the Wazuh-backed ingestion path remains the reviewed intake boundary and does not authorize direct vendor-local actioning or commercial-SIEM-style breadth.

## Cross-Link Review

The design document must remain cross-linked from the source onboarding contract, the asset and identity privilege baseline, and the Wazuh alert ingest contract so the approved family boundary stays reviewable from each dependent artifact.

## Deviations

No deviations found.'
commit_fixture "${missing_validation_repo}"
rm "${missing_validation_repo}/docs/phase-14-identity-rich-source-family-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-14-identity-rich-source-family-validation.md
assert_fails_with "${missing_validation_repo}" "Missing Phase 14 identity-rich source family validation record:"

echo "Phase 14 identity-rich source family verifier tests passed."
