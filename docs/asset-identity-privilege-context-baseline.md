# AegisOps Asset, Identity, and Privilege Context Baseline

## 1. Purpose

This document defines the minimum asset, identity, and privilege context baseline for Phase 7 AI-assisted threat hunting design work.

It supplements `docs/secops-domain-model.md`, `docs/auth-baseline.md`, and `docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md` by defining the smallest reviewed context model AegisOps may use when hunts reason about hosts, users, service accounts, groups, aliases, ownership, and criticality.

This document defines baseline terms, ownership expectations, and bounded reasoning claims only. It does not approve live CMDB integration, IdP integration, or production privilege synchronization.

## 2. First-Class Context Terms

The following terms are first-class context entities for Phase 7 design work:

| Term | Baseline definition |
| ---- | ---- |
| `Asset` | A host, workload, device, application instance, or other operational computing target that may produce telemetry, receive actions, or require ownership context. |
| `Identity` | A human or machine principal that may authenticate, own activity, approve work, or operate automation relevant to hunt and triage context. |
| `Group` | A named collection of identities used for access assignment, administrative delegation, or scoping of privilege-relevant relationships. |
| `Service Account` | A non-human identity used by automation, integrations, monitors, or workflows rather than by an interactive person. |
| `Alias` | A reviewed alternate identifier that may refer to the same asset, identity, or group without asserting hidden authority beyond the mapped context. |
| `Ownership` | The accountable team or role expected to know why the asset or identity exists, what it supports, and who may authorize changes. |
| `Criticality` | A bounded rating that explains how operationally or security-significant an asset, identity, or group is for triage and escalation decisions. |
| `Privilege Context` | The reviewed description of why an identity, group, or asset is security-sensitive because of administrative capability, delegated authority, or access to high-impact systems. |

These terms extend the existing `Asset` and `Identity` reference-entity model rather than replacing it.

`Group`, `Service Account`, `Alias`, `Ownership`, `Criticality`, and `Privilege Context` exist to make threat-hunting explanations explicit before any live enterprise enrichment is introduced.

## 3. Minimal Resolution and Alias Claims

AegisOps may claim direct equality only when two records share the same stable identifier inside the same reviewed source boundary.

AegisOps may claim probable alias linkage only when the relationship is explicitly supplied by reviewed documentation, curated mapping, or analyst-confirmed case context.

AegisOps must not invent transitive identity, host, or group resolution from naming similarity alone.

When resolution is incomplete, the baseline expectation is to preserve the ambiguity explicitly rather than fabricate a single authoritative entity.

At this baseline, reviewed alias handling may support statements such as:

- a hostname and inventory label refer to the same reviewed host;
- a user principal name and directory short name refer to the same reviewed identity;
- a privileged group has a reviewed alternate display name in a local platform; or
- a service account has a stable integration-specific identifier that maps to one reviewed automation identity.

This baseline does not authorize graph expansion, hidden transitive closure, or silent entity stitching across multiple systems just because identifiers appear similar.

## 4. Ownership, Criticality, and Privilege Context Expectations

Each tracked asset should have a named owning team or role, a stated operational purpose, and a criticality expectation when that context is available.

Each tracked identity or service account should have a named owner, expected usage boundary, and whether the identity is interactive, shared, or automation-bound.

Privilege-relevant groups must be treated as context-bearing entities even when live group membership synchronization is out of scope.

Service accounts must remain distinct from human identities in hunt reasoning even if their names resemble individual user identifiers.

The minimum expected context fields for Phase 7 design work are:

| Entity family | Minimum context expectation | Why it matters |
| ---- | ---- | ---- |
| `Asset` | Owner, operational purpose, criticality, and known aliases when available | Lets hunts explain why a host or workload matters without pretending a CMDB is already integrated. |
| `Identity` | Owner, identity type, known aliases, and whether the identity is interactive or machine-bound | Prevents hunts from collapsing people and automation into one ambiguous actor. |
| `Group` | Owner, privilege relevance, and reviewed scope or purpose | Preserves why membership in the group is security-significant. |
| `Service Account` | Owner, automation surface, privilege context, and criticality of the systems it can affect | Distinguishes bounded automation identities from generic usernames. |

Host ownership, business purpose, service-account ownership, group sensitivity, and criticality may inform hunt prioritization and triage explanation, but they do not prove maliciousness by themselves.

Privilege context may include statements such as local administrator scope, domain-adjacent delegated administration, approval authority, secrets access, or control over high-impact infrastructure, but each statement must remain bounded to reviewed source context.

## 5. Hunt and Triage Usage Boundaries

Phase 7 hunt workflows may use this baseline to explain why a host, user, service account, or group deserves additional scrutiny without claiming that AegisOps already has live enterprise authority over those records.

This baseline permits bounded statements such as known owner, declared criticality, reviewed alias, and privilege-relevant group membership only when those statements come from approved internal reference data or analyst-reviewed case context.

Approved Phase 7 reasoning may:

- prioritize a hunt lead because the affected asset is marked critical;
- explain that an identity is a service account rather than a human operator;
- note that membership in a reviewed privileged group raises triage priority; and
- preserve that multiple labels refer to one reviewed asset or identity when the alias mapping is explicit.

Approved Phase 7 reasoning may not:

- claim complete enterprise asset coverage;
- claim complete identity or group coverage across all systems;
- infer missing ownership, aliases, or entitlements from naming patterns alone; or
- describe privilege context as authoritative proof of current access if the repository only holds reviewed design-time context.

This baseline does not make CMDB data authoritative for all asset truth, does not make an IdP authoritative for every entitlement edge, and does not authorize production entitlement automation.

## 6. Explicit Non-Goals

Live CMDB integration is out of scope.

IdP integration for live identity or group synchronization is out of scope.

Production privilege sync, entitlement reconciliation, and automatic authorization changes are out of scope.

This baseline does not define a production-ready schema for enterprise inventory ingestion, directory federation, entitlement graph computation, or continuously updated ownership reconciliation.

This baseline also does not authorize AI-assisted hunts to treat undocumented spreadsheet data, ticket notes, or ad hoc operator memory as hidden authoritative enrichment.

## 7. Baseline Alignment Notes

This baseline keeps asset, identity, group, service-account, alias, ownership, criticality, and privilege context explicit for hunt design without creating a shadow source of truth.

It aligns with the SecOps domain model by keeping contextual reference entities separate from findings, alerts, cases, and evidence.

It aligns with the auth baseline by preserving distinct treatment for human identities, service accounts, approval roles, and least-privilege expectations.

It aligns with the Phase 7 AI hunt ADR by allowing only bounded, reviewable context claims rather than silent live enrichment or externally hosted authority over internal identity and asset records.
