# AegisOps Phase 20 First Live Low-Risk Action and Reviewed Delegation Boundary

## 1. Purpose

This document defines the approved Phase 20 first live low-risk action and the reviewed delegation boundary that connects one narrow live execution path without reopening broader response scope.

It supplements `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/automation-substrate-contract.md`, `docs/response-action-safety-model.md`, `docs/control-plane-state-model.md`, `docs/secops-business-hours-operating-model.md`, and `docs/architecture.md`.

This document defines one approved low-risk live action, the operator-to-approval-to-delegation boundary for that action, and the required fail-closed binding checks only. It does not approve broader ticketing automation, wider notification catalogs, policy-authorized unattended execution, or high-risk live executor wiring.

## 2. Approved First Live Low-Risk Action

The approved first live low-risk action for Phase 20 is `notify_identity_owner`.

This action is the reviewed single-recipient owner-notification path for one accountable human owner or explicitly designated escalation contact tied to the in-scope alert, case, and evidence set already reviewed inside AegisOps.

The Phase 20 live action stays in the `Notify` safety class and must not mutate the protected target, target-side configuration, case authority, or approval truth.

The approved first live path is intentionally narrower than a general notification framework. It is limited to a single-recipient owner-notification path rather than ticket creation, chat-room fanout, pager trees, broad stakeholder broadcast, or any action that implicitly changes workflow ownership outside the reviewed case.

The approved first live action must remain anchored to the completed Phase 19 operator slice and the reviewed Phase 13 delegation model rather than creating a new standalone automation surface.

For the approved security mainline, that routine automation surface is Shuffle only.

## 3. Approved Action Shape

The reviewed `notify_identity_owner` payload must stay specific enough that approval and reconciliation remain bound to one reviewed intent.

At minimum, the approved payload must identify:

- `action_type` with the exact value `notify_identity_owner`;
- the reviewed target record such as the single `asset_id` or equivalent approved identity-linked scope used during approval binding;
- the single approved recipient identity or designated escalation contact resolved by AegisOps before delegation;
- the reviewed message intent and escalation reason tied to the linked alert, case, recommendation, and evidence set; and
- the reviewed execution surface binding for `automation_substrate` and `shuffle`.

The approved first live action must not let Shuffle choose the recipient, widen the audience, rewrite the message into a materially different escalation, open tickets, mutate source systems, or infer new response scope from vendor-local workflow logic.

## 4. Operator-to-Approval-to-Delegation Boundary

The approved Phase 20 path is:

`reviewed Phase 19 casework -> explicit action request -> human approval -> reviewed Shuffle delegation -> authoritative reconciliation`

Phase 20 does not approve a direct queue-to-execution shortcut. The operator workflow must stay grounded in the Phase 19 reviewed operator surface and linked evidence before any live delegation occurs.

### 4.1 Human-Owned Steps

The following steps remain human-owned in Phase 20:

- deciding that the in-scope case requires external owner notification rather than more casework, closure, or a higher-risk response path;
- identifying the single approved recipient or designated escalation contact and confirming the contact is the correct accountable human boundary for the reviewed case;
- defining the message intent, escalation reason, and any required case or evidence references before approval;
- issuing the explicit action request inside AegisOps with the reviewed target scope, recipient, message intent, payload, and expiry;
- issuing the human approval decision that binds the exact reviewed payload and time window; and
- reviewing any reconciliation exception, duplicate delivery signal, stale execution state, or downstream mismatch before any retry or follow-up occurs.

Phase 20 keeps the human approver in the loop even though Phase 13 established a broader low-risk routing capability. Policy-authorized unattended low-risk execution remains deferred until a later reviewed phase narrows that broader authority explicitly.

### 4.2 Shuffle-Delegated Steps

Shuffle is delegated only the bounded transport task after AegisOps has already created the reviewed request and approval records.

The following steps may be delegated to Shuffle:

- receive the reviewed delegation record for the already-approved `notify_identity_owner` intent;
- execute the already-bound notification transport on the approved low-risk automation surface; and
- return the execution run identifier and downstream status evidence that AegisOps later correlates back into authoritative `Action Execution` and `Reconciliation` records.

Shuffle must not become the authority for action intent, recipient selection, approval truth, execution truth, or reconciliation truth.

## 5. Required Binding and Expiry Checks

The Phase 20 live path must preserve the reviewed Phase 13 delegation identity and binding requirements in full.

At minimum, the live delegation must preserve:

- `action_request_id`;
- `approval_decision_id`;
- `delegation_id`;
- `execution_surface_type`;
- `execution_surface_id`;
- `idempotency_key`;
- `payload_hash`; and
- the approved expiry window carried by the approval and request records.

Before delegation, AegisOps must prove that the current action request, approval decision, and downstream execution surface still match the reviewed intent exactly.

The approval record must remain immutable enough that AegisOps can compare the current request against the approved expiry window and the reviewed payload binding instead of trusting mutable request state alone.

The Phase 20 path must fail closed when:

- the approved payload no longer matches the action request target scope, recipient binding, or reviewed execution surface;
- the approved expiry window does not match the action request expiry;
- the approval decision is no longer approved at delegation time;
- the request is routed to any execution surface other than `automation_substrate` on `shuffle`; or
- downstream execution evidence arrives without the reviewed binding identifiers needed to correlate the run back to the approved delegation.

## 6. Reconciliation Expectations

AegisOps remains authoritative for request, approval, execution, and reconciliation truth on the Phase 20 live path.

Shuffle receipts, vendor run identifiers, and delivery status are downstream evidence only. They do not replace the AegisOps-owned `Action Execution` or `Reconciliation` record families.

If Shuffle reports:

- a duplicate run for the same `idempotency_key`,
- a status update for the wrong execution surface,
- a run without the approved delegation identity,
- a payload mismatch, or
- a stale or missing execution result after the approved window,

then AegisOps must preserve that condition as explicit reconciliation state and fail closed instead of normalizing it into a successful notification.

## 7. Deferred Beyond Phase 20

The following remain deferred beyond Phase 20:

- any broader action catalog beyond `notify_identity_owner`;
- multi-recipient escalation fanout, ticket creation, chat-room broadcast, or workflow-side recipient discovery;
- policy-authorized unattended low-risk execution;
- any medium-risk or high-risk live action wiring;
- isolated-executor live activation for production execution paths;
- broader workflow orchestration that chains notification into approval, ticketing, mutation, or follow-on response steps; and
- any change that makes Shuffle, another substrate, or workflow-local state the authority for request, approval, execution, or reconciliation truth.

## 8. Alignment and Non-Expansion Rules

`docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md` remains the normative source for the reviewed operator surface that precedes any Phase 20 action request.

`docs/automation-substrate-contract.md` remains the normative source for `approval_decision_id`, `delegation_id`, `idempotency_key`, `payload_hash`, and execution-surface binding expectations.

`docs/response-action-safety-model.md` remains the normative source for the `Notify` safety class and the rule that recipient and escalation intent must be explicit before execution.

`docs/control-plane-state-model.md` remains the normative source for the rule that AegisOps owns authoritative `Action Execution` and `Reconciliation` records.

`docs/secops-business-hours-operating-model.md` remains the normative source for the rule that explicit human escalation stays bounded to designated human owners and does not silently convert the platform into 24x7 autonomous response.

`docs/architecture.md` remains the normative source for the rule that Shuffle is an approved execution substrate and must not become the authority for policy-sensitive workflow truth.
