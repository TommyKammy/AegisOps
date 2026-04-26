# Pilot Pause, Rollback, and Exit Criteria

## 1. Purpose and Boundary

This document defines reviewed pause, rollback, continue, exit, unresolved-limitation, and next-roadmap capture criteria for the single-customer pilot.

The decision surface is operational and reviewable. It is not a customer commercial terms sheet, public launch checklist, SLA acceptance record, multi-customer rollout gate, or multi-tenant expansion plan.

Pilot pause, rollback, continue, and exit decisions remain subordinate to AegisOps authoritative records, the pilot readiness decision, support playbook evidence, operator handoff evidence, and the restore, rollback, and upgrade release-gate rehearsal.

## 2. Decision Record

Every pilot health review that considers pause, rollback, continue, or exit must record:

- the reviewed release identifier or repository revision;
- the named pilot owner, operator, support reviewer, and handoff owner;
- the linked pilot readiness decision, support evidence note, operator handoff entry, runtime smoke manifest, rollback evidence record, known-limitation review, and next health review;
- the decision: continue, pause, rollback, exit-success, exit-no-go, or capture-next-roadmap-input; and
- the refusal reason and clean-state evidence when the decision is pause, rollback, exit-no-go, rejected, forbidden, or failed.

The decision must use directly linked AegisOps records and retained evidence. Operators must not infer customer, tenant, ticket, detector, assistant, release, or rollback linkage from naming conventions, nearby notes, ticket state, assistant output, raw forwarded headers, or substrate-local status.

## 3. Pilot Pause Criteria

Pause the pilot and keep normal operator use blocked when any of the following are true:

- release readiness, runtime smoke, detector activation scope, Zammad coordination scope, assistant limitation, known-limitation, support, or handoff evidence is missing, stale, mixed across release identifiers, or only partially trusted;
- a runtime, detector, coordination, assistant, evidence, or support degradation cannot be corrected inside the reviewed business-hours health-review window without widening pilot scope;
- support expectations would require 24x7 coverage, customer-specific paid support terms, emergency authority bypass, direct backend access, or customer-private secret exposure;
- an unresolved limitation affects launch, normal operation, rollback acceptance, detector disable, Zammad coordination, assistant output, evidence handoff, or operator training and lacks an owner, disposition, review date, or clean-state proof; or
- the operator cannot explain the queue, case, action-review, approval, execution, reconciliation, evidence handoff, and next-owner path from directly linked reviewed records.

Pause is a reviewed hold state, not a silent success, informal support escalation, commercial renegotiation, or permission to keep operating with guessed prerequisites.

## 4. Rollback Criteria

Escalate to rollback when the pilot cannot continue or pause safely on the current release because runtime, detector, coordination, assistant, support, evidence, or handoff drift would leave reviewed records ambiguous or untrustworthy.

Rollback must align with `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md` and retain:

- same-day rollback decision owner;
- selected restore point and restore target;
- pre-change backup custody and reviewed configuration reference;
- before-and-after repository revision or release identifier;
- runtime smoke result after rollback where feasible;
- reviewed record-chain evidence;
- refusal reason for failed, rejected, forbidden, or restore-failure paths; and
- clean-state proof that no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived the attempt.

Rollback does not authorize direct source-side mutation, vendor-specific backup product dependency, HA choreography, direct backend exposure, optional-extension launch gates, ticket-system authority, assistant-owned workflow decisions, or customer-private production access.

## 5. Exit and Success Criteria

Exit-success is allowed only when the reviewed pilot record shows that the single-customer operating path stayed bounded and trustworthy for the reviewed pilot window.

The exit-success decision must name:

- the reviewed release identifier or repository revision;
- release readiness and runtime smoke evidence;
- detector activation, disable, rollback, expected-volume, false-positive, and next-review evidence for the accepted detector scope;
- Zammad coordination posture and credential custody without treating tickets as AegisOps authority;
- assistant advisory-only limitation evidence;
- known limitations with dispositions, owners, and review dates;
- operator and support signoff that the queue, case, action-review, reviewed-record, non-authority, pause, rollback, and evidence handoff paths are understood; and
- the next roadmap input record, if any, without changing Phase 43 scope.

Exit-no-go is required when the pilot cannot prove those criteria, when rollback or clean-state evidence is missing after a failed path, or when the outcome would depend on customer commercial terms, public launch readiness, multi-customer rollout assumptions, or multi-tenant expansion criteria.

## 6. Unresolved Limitations and Next-Roadmap Input

Unresolved limitations must be handled as reviewed records with a disposition of block, accept-with-owner, rollback, disable, support-follow-up, or capture-next-roadmap-input.

Each unresolved limitation must name the operator-visible behavior, affected surface, owner, next review, evidence link, and whether it changes pilot pause, rollback, continue, or exit status.

Next-roadmap input may capture candidate follow-up work from the pilot, but it must remain separate from Phase 43 acceptance. Captured input must not turn customer commercial terms, public launch checklist items, multi-customer rollout requirements, multi-tenant expansion criteria, optional-extension launch gates, or broad support promises into current pilot scope.

## 7. Operator and Support Signoff Checklist

Before continuing after a pause, accepting rollback completion, or recording exit-success, operator and support signoff must confirm:

- the support playbook was reviewed for degradation and break-glass handling;
- the operator training packet was reviewed for queue, case, action-review, reviewed-record, non-authority, and evidence handoff practice;
- the pilot owner, support reviewer, operator, handoff owner, next health review, and any follow-up owner are named;
- failed, rejected, forbidden, rollback, restore, pause, and no-go paths retain refusal reason plus clean-state proof; and
- no signoff relies on workstation-local absolute paths, live secrets, placeholder credentials, raw forwarded headers, ticket authority, assistant authority, optional-extension health, or inferred scope.

## 8. Verification

Verify this criteria document with `scripts/verify-pilot-pause-rollback-exit-criteria.sh`.

Negative validation for the verifier is `scripts/test-verify-pilot-pause-rollback-exit-criteria.sh`.

Run the verifier after changing this document, the runbook, pilot readiness checklist, support playbook, operator training packet, release handoff package, operational evidence handoff pack, or restore rollback upgrade evidence rehearsal.

## 9. Out of Scope

Customer commercial terms, formal SLA commitments, public launch checklist ownership, hosted release channels, multi-customer rollout, multi-tenant expansion criteria, direct customer-private production access, direct backend exposure, optional-extension launch gates, ticket-system authority, assistant-owned workflow authority, and broad support promises beyond the reviewed business-hours single-customer pilot are out of scope.
