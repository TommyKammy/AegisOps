# AegisOps Phase 46 Approval, Execution, and Reconciliation Operations Pack Boundary

## 1. Purpose

This document defines the reviewed Phase 46 approval, execution, and reconciliation operations pack boundary.

It retroactively closes the Phase 46 contract around the approval role matrix, approval fallback and escalation rehearsal, reconciliation mismatch closeout, Zammad non-authority rehearsal, and focused Zammad verifier self-test fixtures.

It supplements `docs/runbook.md`, `docs/response-action-safety-model.md`, `docs/control-plane-state-model.md`, `docs/secops-domain-model.md`, `docs/phase-30d-approval-execution-reconciliation-ui-boundary.md`, `docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md`, `docs/operations-zammad-live-pilot-boundary.md`, `docs/deployment/operator-training-handoff-packet.md`, and `docs/deployment/support-playbook-break-glass-rehearsal.md`.

This document describes the closed Phase 46 operations pack contract only. It does not change approval behavior, execution behavior, reconciliation behavior, Zammad behavior, runtime behavior, role classes, action types, or production RBAC design.

## 2. In Scope

Phase 46 closes one narrow operations pack contract:

- the approval role matrix in `docs/runbook.md` remains the reviewed handoff source for approver, fallback approver, platform admin, operator, and support owner responsibilities;
- approval fallback and escalation rehearsal remains evidence over AegisOps action request and approval decision records, not a shortcut around approval;
- reconciliation mismatch closeout remains anchored to the AegisOps reconciliation record and directly linked execution receipt;
- Zammad non-authority rehearsal remains link-first, coordination-only, and subordinate to AegisOps records;
- focused Zammad verifier self-test fixtures remain the checked negative path for available, degraded, and unavailable coordination states; and
- operator training and support playbook references remain aligned to the same approval, execution, reconciliation, coordination, and authority split.

Phase 46 is an operations-pack documentation closure. It records that maintainers can understand the reviewed approval-to-reconciliation posture from repo-owned artifacts without promoting tickets, downstream receipts, browser state, assistant output, or support notes into workflow truth.

## 3. Out of Scope

Phase 46 does not authorize:

- a new approval model or new role classes;
- a new execution behavior, executor, action type, or dispatch path;
- a new reconciliation semantic, closure state, or mismatch policy;
- Phase 49 production RBAC design;
- ticket-driven case closure, approval, execution, reconciliation, or readiness;
- treating Zammad, external ticket state, downstream receipts, comments, credential placeholders, browser state, assistant output, or support notes as authoritative; or
- storing live credentials, endpoint secrets, bearer tokens, API keys, private keys, or customer credentials in docs, fixtures, issue text, or operator prompts.

Zammad close does not close AegisOps case. Ticket comments, ticket status, assignee changes, SLA state, queue state, priority, escalation, or closure may be retained only as subordinate coordination context when an AegisOps record explicitly binds that context.

## 4. Approval Role Matrix

The approval role matrix in `docs/runbook.md` is the reviewed Phase 46 authority map.

The reviewed responsibilities remain:

- `Approver`: reviews the exact AegisOps action request, linked case, requested scope, evidence, risk, and expiry window before recording approve or deny on the AegisOps approval decision record.
- `Fallback approver`: acts only when the primary approver is unavailable or the approval window would otherwise expire, while preserving the fallback reason, time window, and unchanged scope limits.
- `Platform admin`: maintains identity, role binding, runtime, and secret-custody plumbing, but does not approve an action unless separately named as the approver for that request.
- `Operator`: prepares the action request, evidence bundle, and routing note, then waits for the reviewed approval outcome instead of self-approving, executing, or treating a ticket comment as approval.
- `Support owner`: coordinates degradation, denial, timeout, fallback, break-glass follow-up evidence, and next-owner handoff, but does not approve, execute, reconcile, or redefine AegisOps workflow truth.

These are named responsibilities inside the existing AegisOps approval model. They are not new role classes and do not create customer-specific support authority or external-ticket-driven workflow truth.

## 5. Fallback and Escalation Rehearsal

Fallback and escalation rehearsal evidence is anchored in `control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json` and verified by `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`.

The fixture includes Phase 46 denial, fallback, and escalation scenarios that preserve:

- the action request identifier;
- the approval decision identifier when a decision exists;
- the approver or fallback actor identity;
- the denial, timeout, fallback, or escalation reason;
- the unchanged action scope and linked evidence expectation; and
- the fact that no executor dispatch or reconciliation success is inferred when approval remains denied, pending, escalated, or only manually followed up.

Fallback approval handling requires a named fallback approver or fallback actor, the reason the primary approver could not decide inside the reviewed window, the unchanged action scope, and evidence that the fallback did not widen authority.

Escalation rehearsal preserves pending human accountability. It must not approve, execute, reconcile, or close the reviewed action by implication.

Break-glass closeout remains a recovery closeout path only. It must document custody, reviewer, bounded window, affected binding, rotation or invalidation evidence, readiness or refusal check, clean-state proof, and return-to-normal owner without converting break-glass use into approval, execution, or reconciliation authority.

## 6. Execution and Reconciliation Separation

Approval, execution, and reconciliation remain separate first-class records.

The required split is:

- the `Approval Decision` record says whether the exact request is allowed for the reviewed scope and window;
- the `Action Execution` record says what the reviewed execution surface attempted, refused, or reported; and
- the `Reconciliation` record says whether the observed outcome matches, mismatches, fails to prove, or remains stale against the approved intent.

Execution success is not reconciliation success. A downstream completed status, executor receipt, ticket comment, browser-rendered state, support note, or assistant summary must not close reconciliation.

Reconciliation mismatch closeout must name the expected AegisOps state separately from the received substrate receipt. A matched reconciliation may be closed only with the AegisOps reconciliation identifier, comparison time, execution receipt reference, and linked evidence retained as closeout evidence. A mismatched reconciliation remains open until an operator reviews the mismatch summary against the approved action scope and records the corrected AegisOps outcome. A stale or missing receipt remains action-required until a fresh authoritative receipt is obtained or the missing receipt is explicitly escalated.

## 7. Zammad Non-Authority Rehearsal

The Zammad non-authority rehearsal is anchored in `docs/operations-zammad-live-pilot-boundary.md` and `control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json`.

Zammad remains the first live coordination substrate for the pilot, but it remains coordination-only. Zammad and downstream receipts remain non-authoritative.

The rehearsal fixture covers:

- `available` coordination when reviewed credential custody, endpoint, and explicit AegisOps linkage exist;
- `degraded` coordination when stale or mismatched ticket evidence must remain visible without becoming truth; and
- `unavailable` coordination when missing, placeholder, fake, sample, TODO, empty, stale, unsigned, or unreviewed credentials block live-available posture.

Operators may inspect a reviewed Zammad ticket pointer, URL, or bounded coordination status when it is explicitly linked to an AegisOps case or action-review record. They must not infer case existence, approval, execution, reconciliation, closure, customer notification, or readiness from ticket state, ticket closure, comments, assignee, SLA, queue, priority, escalation, or downstream receipt text.

No failed Zammad write, stale read, timeout, proxy failure, auth failure, degraded payload, placeholder credential, browser session, or ticket close may create an orphan AegisOps authority record or mark an AegisOps lifecycle step complete.

## 8. Focused Zammad Verifier Self-Test Fixtures

The focused Zammad verifier self-test fixtures are locked by `scripts/test-verify-zammad-live-pilot-boundary.sh`.

The self-test must prove that `scripts/verify-zammad-live-pilot-boundary.sh` fails closed when the Zammad boundary or fixture omits the reviewed non-authority posture, credential custody posture, unavailable or degraded behavior, explicit AegisOps linkage, or workstation-local path hygiene.

The positive verifier path must continue to confirm:

- `docs/operations-zammad-live-pilot-boundary.md` exists and keeps Zammad as the single first live pilot substrate;
- `control-plane/tests/test_issue812_zammad_live_pilot_boundary_docs.py` exists and covers the live pilot docs contract;
- `control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json` exists and covers available, degraded, and unavailable scenarios; and
- Zammad ticket state cannot become case, action, approval, execution, or reconciliation authority.

## 9. Fail-Closed Conditions

Phase 46 must fail closed when any prerequisite approval, execution, reconciliation, coordination, credential, provenance, scope, or linkage signal is missing, malformed, placeholder-like, mixed, stale, or only partially trusted.

Blocking conditions include:

- approval records do not bind the exact requester, approver, target snapshot, payload hash, approval timestamp, expiry, outcome, and required scope;
- fallback approval evidence lacks a named fallback actor, fallback reason, unchanged scope, or proof that authority was not widened;
- escalation notes imply approval, execution, reconciliation, closure, or return to normal without the reviewed AegisOps record;
- execution receipts are treated as approval or reconciliation truth;
- reconciliation closeout lacks the AegisOps reconciliation identifier, execution receipt reference, comparison time, linked evidence, or corrected AegisOps outcome for mismatches;
- ticket closure, comments, SLA state, queue state, priority, assignee, support note, browser state, assistant output, downstream receipt text, or optional substrate status overrides AegisOps records;
- missing, placeholder, fake, sample, TODO, empty, stale, unsigned, or personal-session credentials are accepted as live Zammad custody;
- raw forwarded headers, host, proto, tenant, or user identity hints are trusted without a reviewed authenticated boundary; or
- documentation, validation commands, fixtures, or operator notes introduce workstation-local absolute paths, hidden manual steps, live secrets, or production write behavior.

When one of these conditions appears, the correct outcome is blocked execution, explicit denial, explicit unresolved or degraded state, unavailable coordination posture, refusal, or a documented follow-up. The system must not infer success from names, path shape, ticket status, receipt wording, browser visibility, cached context, or nearby metadata.

## 10. Authority Boundary Notes

AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, approval, action intent, execution receipt, reconciliation, lifecycle, readiness, release, pilot entry, and audit truth.

Approval truth remains the AegisOps approval decision record.

Execution truth remains the AegisOps action-execution record and linked reviewed receipt.

Reconciliation truth remains the AegisOps reconciliation record.

Zammad, external ticket state, downstream receipts, comments, credential placeholders, browser state, assistant output, support notes, and optional substrate health remain subordinate context only.

Approval, execution, and reconciliation remain separate first-class records and must not be collapsed into one status badge, ticket state, support note, or downstream receipt.

## 11. Validation Expectations

Validation must remain documentation and boundary focused.

At minimum, validation should prove:

- the Phase 46 boundary and validation docs exist;
- the docs name in-scope, out-of-scope, fail-closed conditions, verifier references, and authority boundary notes;
- the approval role matrix remains anchored to `docs/runbook.md`;
- fallback and escalation rehearsal remains anchored to the reviewed record-chain fixture and verifier;
- reconciliation mismatch closeout preserves approval, execution, and reconciliation separation;
- Zammad close does not close AegisOps case;
- Zammad and downstream receipts remain non-authoritative;
- focused Zammad verifier self-test fixtures still cover available, degraded, and unavailable coordination states; and
- no approval, execution, reconciliation, Zammad, or runtime behavior change is included.
