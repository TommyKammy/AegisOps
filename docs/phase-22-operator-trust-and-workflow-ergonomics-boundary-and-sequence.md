# AegisOps Phase 22 Operator Trust and Workflow Ergonomics Boundary and Sequence

## 1. Purpose

This document defines the reviewed Phase 22 operator trust and workflow ergonomics boundary for the already-approved reviewed action path.

It supplements `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md`, `docs/phase-21-production-like-hardening-boundary-and-sequence.md`, `docs/control-plane-state-model.md`, `docs/automation-substrate-contract.md`, `docs/response-action-safety-model.md`, `docs/secops-business-hours-operating-model.md`, and `docs/architecture.md`.

This document defines visibility, review semantics, mismatch taxonomy, handoff visibility, and implementation sequencing only. It does not approve a new live action class, a broader execution substrate, or a broader operator redesign.

## 2. Reviewed Phase 22 Boundary

The approved Phase 22 boundary is a review and ergonomics phase around the already-approved Phase 19 through Phase 21 path rather than a new execution-breadth phase.

Phase 22 is limited to making the reviewed operator-facing action chain easier to inspect, hand off, and trust without changing who owns approval authority, delegation authority, execution truth, or reconciliation truth.

The approved Phase 22 path is:

`Action Request -> Approval Decision -> Delegation -> Action Execution -> Reconciliation`

Phase 22 therefore narrows work to operator visibility and reviewed record shape for the existing path instead of broadening the action catalog, source breadth, or authority model.

Phase 22 must preserve the completed Phase 19 through Phase 21 fail-closed boundaries and the reviewed Phase 20 approval / delegation / reconciliation binding guarantees.

## 3. Operator Visibility Contract

The operator visibility contract for Phase 22 is the minimum reviewed surface that lets an analyst or approver understand where one action stands without reconstructing status from raw workflow logs, indirect queue drift, or substrate-local history.

At minimum, queue, alert, and case views must keep the following action-review fields visible for one reviewed action chain:

- current `Action Request` status and immutable request identity;
- current `Approval Decision` status, approver identity, and expiry window;
- current `Delegation` status with binding identifiers and downstream execution-surface reference;
- current `Action Execution` status with attributable execution evidence or mismatch preservation; and
- current `Reconciliation` status with any explicit disagreement still awaiting review.

The queue view is the skim surface. It must show enough reviewed status to identify whether an item is waiting for approval, blocked by expiry or rejection, affected by mismatch, or handed off for later review.

The alert view is the source-linked inspection surface. It must preserve how the current action-review state relates to the alert, evidence, recommendation, and escalation context without forcing the operator to inspect execution logs first.

The case view is the durable coordination surface. It must preserve the current authoritative action-review state, handoff notes, escalation notes, manual fallback notes, and next-step expectation for the reviewed case.

Phase 22 does not approve a new separate operator console, a new dashboard-first interaction model, or workflow-local status as the authoritative source of truth for operator review.

## 4. Reviewed Approval State Semantics

Phase 22 must make the reviewed approval state classes explicit across queue, alert, and case views so the same status means the same thing everywhere.

Pending means the action request exists, the reviewed approval decision is not yet resolved, and no delegation or execution may proceed.

Expired means the reviewed approval window closed before a valid delegation consumed the approved request.

Rejected means an approver explicitly denied the reviewed action request for the current payload and scope.

Superseded means a later reviewed request or approval record replaced the earlier candidate before execution.

These approval state classes are minimum reviewed visibility requirements for queue, alert, and case views:

- `pending` must show the current approver expectation, expiry window, and next reviewer action rather than only a generic waiting label;
- `expired` must remain visible as non-executed review state until an operator closes or supersedes it with a new reviewed request;
- `rejected` must preserve rejection visibility, reviewer attribution, and the next expected case or alert follow-up instead of disappearing from the workflow surface; and
- `superseded` must preserve linkage to the replacing reviewed request or approval record so operators can understand which candidate is authoritative.

Phase 22 must not let queue, alert, or case views silently normalize `expired`, `rejected`, or `superseded` into generic closed or cleared states when action review is still operationally relevant.

## 5. Mismatch Taxonomy and Inspection Expectations

The reviewed mismatch taxonomy is limited to delegation mismatch, execution mismatch, and reconciliation mismatch.

Delegation mismatch means the reviewed request, approval, payload hash, recipient or target scope, expiry, idempotency key, or execution-surface binding no longer matches the records that would govern delegation.

Execution mismatch means downstream execution evidence exists, but the reviewed execution attempt no longer matches the approved delegation identity, execution-surface expectation, or actor attribution needed to trust the result.

Reconciliation mismatch means AegisOps cannot reconcile the authoritative `Action Execution` record and the authoritative `Reconciliation` record with downstream evidence without preserving an explicit disagreement state.

The minimum reviewed inspection expectations for mismatch handling are:

- delegation mismatch must show the exact binding class that drifted and must block delegation until a human reviews the mismatch;
- execution mismatch must show the execution evidence, the expected approved delegation identity, and why the result cannot be trusted as authoritative success;
- reconciliation mismatch must show what disagrees across the approved request, authoritative execution record, and downstream evidence so a reviewer can resolve the disagreement deliberately; and
- all mismatch classes must remain visible in queue, alert, or case review until explicitly resolved, superseded, or closed by reviewed follow-up.

Phase 22 must preserve mismatch visibility as operator-facing review state rather than burying mismatch detail only in backend diagnostics or workflow-local history.

## 6. Reviewed Record Requirements for Handoff and Fallback

The minimum reviewed record additions in Phase 22 are manual fallback visibility, after-hours handoff visibility, escalation-note visibility, and actor identity display expectations.

### 6.1 Manual Fallback

Manual fallback visibility must preserve:

- the original `Action Request` and `Approval Decision` identifiers;
- why the reviewed delegated workflow path was unavailable, inappropriate, or intentionally not used;
- who performed the manual fallback and under which role or authority boundary;
- what action was actually carried out and when; and
- what post-action verification evidence or residual uncertainty remains open.

Manual fallback must remain an attributed exception path. Phase 22 must not present manual fallback as equivalent to an approved delegated success when the execution path differed.

### 6.2 After-Hours Handoff

After-hours handoff visibility must preserve:

- whether the item can wait for business-hours review or required explicit human escalation;
- whether an action is still `pending`, has `expired`, was `rejected`, or was `superseded`;
- which evidence, notes, and mismatch state the next analyst must inspect first;
- which human was notified or handed off work after hours; and
- what next review deadline, follow-up expectation, or business constraint still applies.

Phase 22 must keep after-hours handoff review inside the same authoritative queue, alert, and case record chain rather than relying on ad hoc chat fragments or workflow-run history.

### 6.3 Escalation Notes

Escalation notes must be visible enough that the next operator can determine:

- why waiting was unsafe or unacceptable;
- which accountable human owner, designated escalation contact, or approver boundary was engaged;
- what recommendation, approval, or action-review state existed at the time of escalation; and
- what unresolved mismatch, fallback, or follow-up obligations remain.

Escalation notes remain reviewed operator context. They must not become a hidden side channel that changes authority without corresponding control-plane records.

### 6.4 Actor Identity Display

Actor identity display must distinguish at minimum:

- requesting analyst identity;
- approving human identity;
- delegated execution-surface identity;
- manual fallback actor identity when fallback occurs; and
- reconciliation reviewer identity when mismatch or drift is resolved.

Actor identity display must prefer attributable human or machine identities already approved in the existing boundary instead of generic labels such as "system" or "workflow" when more precise reviewed identity exists.

Phase 22 must not expand actor identity display into policy-authorized AI actioning or ambiguous assistant authority.

## 7. Fixed Implementation Sequence

The fixed reviewed Phase 22 implementation order is:

`approval state semantics -> mismatch inspection contract -> handoff and manual fallback visibility -> actor identity display -> queue, alert, and case view alignment -> focused validation updates`

The sequence stays narrow because each later step depends on the earlier step defining the reviewed state model instead of inventing operator-facing status rules ad hoc during implementation.

Sequence rules:

1. `approval state semantics` comes first so queue, alert, and case views do not invent conflicting meanings for pending, expired, rejected, or superseded.
2. `mismatch inspection contract` comes second so delegation, execution, and reconciliation disagreement remains explicit before visibility work broadens.
3. `handoff and manual fallback visibility` comes third so after-hours and exception handling preserve the same reviewed state chain.
4. `actor identity display` comes fourth so attribution is layered onto already-defined reviewed states and mismatch classes.
5. `queue, alert, and case view alignment` comes fifth so those views render one reviewed contract instead of diverging per surface.
6. `focused validation updates` comes last so repository-local doc verification and child issues implement against one fixed reviewed design.

## 8. Explicit Out of Scope and Non-Expansion Rules

Phase 22 does not approve a new live action class, broad browser-first redesign, or AI authority expansion.

The following remain explicitly out of scope for Phase 22:

- any broader action catalog beyond the completed Phase 20 `notify_identity_owner` path;
- any direct execution shortcut that bypasses reviewed approval, delegation, or reconciliation records;
- any broad browser-first redesign of the operator surface beyond the minimum reviewed visibility contract;
- any new autonomous assistant path, AI-generated approval authority, or AI-owned execution decision;
- any shift of authoritative workflow truth from AegisOps into Shuffle, another substrate, or workflow-local browser state; and
- any change that weakens fail-closed handling for approval drift, delegation drift, execution mismatch, or reconciliation mismatch.

Phase 22 improves operator trust by making the existing narrow path more inspectable, not by widening who can act or what can be executed.

## 9. Alignment and Governing Contracts

`docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md` remains the normative source for the reviewed queue, alert, casework, evidence, and cited-advisory operator path that Phase 22 must not broaden into a general dashboard.

`docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md` remains the normative source for the completed first live action path, the human-owned approval boundary, and the reviewed delegation contract that Phase 22 makes more visible rather than more permissive.

`docs/phase-21-production-like-hardening-boundary-and-sequence.md` remains the normative source for the production-like hardening floor that Phase 22 inherits and must not reopen.

`docs/control-plane-state-model.md` remains the normative source for AegisOps-owned `Action Request`, `Approval Decision`, `Action Execution`, and `Reconciliation` truth.

`docs/automation-substrate-contract.md` remains the normative source for delegation identity, payload binding, expiry, idempotency, and execution-surface binding expectations.

`docs/response-action-safety-model.md` remains the normative source for approval-bound safety classes and action-request versus approval-decision separation.

`docs/secops-business-hours-operating-model.md` remains the normative source for manual fallback, approval timeout review, after-hours escalation, and business-hours handoff expectations.

`docs/architecture.md` remains the normative source for the rule that AegisOps owns the policy-sensitive workflow truth and that reviewed automation substrates must not become the operator authority surface.
