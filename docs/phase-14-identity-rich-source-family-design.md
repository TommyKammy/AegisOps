# AegisOps Phase 14 Identity-Rich Source Family Design

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

The reviewed GitHub audit onboarding package lives at `docs/source-families/github-audit/onboarding-package.md`, and the reviewed analyst triage runbook lives at `docs/source-families/github-audit/analyst-triage-runbook.md`.

### 4.2 Entra ID

| Aspect | Review expectation |
| ---- | ---- |
| Source identity | Tenant, directory, and audit category remain explicit. |
| Actor | Human user, service principal, managed identity, or administrative actor must remain attributable when present. |
| Target | User, group, role assignment, app registration, credential object, or policy object remains explicit. |
| Privilege | Admin role grant, delegated permission, group membership, consent, or credential change context must remain reviewable. |
| Provenance | Operation name, activity time, correlation id, tenant, and initiatedBy / targetResources structure must remain preserved. |

Entra ID signals are expected to provide the strongest directory and privilege context for analyst triage and approval review.

The reviewed Entra ID onboarding package lives at `docs/source-families/entra-id/onboarding-package.md`, and the reviewed analyst triage runbook lives at `docs/source-families/entra-id/analyst-triage-runbook.md`.

### 4.3 Microsoft 365 audit

| Aspect | Review expectation |
| ---- | ---- |
| Source identity | Tenant and workload boundary remain explicit. |
| Actor | User, admin, or service identity must remain attributable when present. |
| Target | Mailbox, site, document, team, policy, sharing link, or message object remains explicit. |
| Privilege | Administrative action, sharing change, consent, retention change, or policy update context must remain reviewable. |
| Provenance | Workload, operation, record type, actor id, target id, and event time must remain preserved. |

Microsoft 365 audit signals are expected to broaden approval-context coverage without becoming a generic platform-wide telemetry grab bag.

The reviewed Microsoft 365 audit onboarding package lives at `docs/source-families/microsoft-365-audit/onboarding-package.md`, and the reviewed analyst triage runbook lives at `docs/source-families/microsoft-365-audit/analyst-triage-runbook.md`.

## 5. Explicit Non-Goals

No direct vendor-local actioning, generic network-wide coverage, or commercial-SIEM-style breadth is approved in Phase 14.

This phase does not approve live identity sync, permission reconciliation, or automatic enforcement based on these families alone.

## 6. Baseline Alignment Notes

This design must remain aligned with `docs/source-onboarding-contract.md` and `docs/asset-identity-privilege-context-baseline.md`.

It also remains aligned with `docs/wazuh-alert-ingest-contract.md` and `docs/architecture.md` by keeping Wazuh as the reviewed ingestion path and AegisOps as the authority for downstream workflow state.
