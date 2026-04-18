# AegisOps Phase 26 First Reviewed Create-Tracking-Ticket Soft-Write Contract

## 1. Purpose

This document defines the first reviewed `create_tracking_ticket` soft-write contract for the Phase 26 coordination boundary.

It supplements `docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary.md`, `docs/response-action-safety-model.md`, and `docs/control-plane-state-model.md` by making the first bounded outbound coordination write explicit before later implementation issues introduce adapters, approval wiring, or live downstream ticket creation.

This document defines the reviewed soft-write contract only. It does not approve generalized ticket lifecycle control, bidirectional synchronization, approval by ticket state, or downstream case ownership.

## 2. Authority and Safety Boundary

`create_tracking_ticket` remains a bounded `Soft Write` coordination action.

AegisOps remains authoritative for case, approval, action-execution, and reconciliation truth.

The downstream coordination target is allowed to receive one reviewed create request and return one reviewed receipt. That downstream receipt is coordination evidence only; it must not become the lifecycle owner for the linked case, approval decision, action execution, or reconciliation outcome.

Only the reviewed coordination ticket create payload may leave AegisOps.

The first reviewed payload is limited to reviewed coordination fields and must not export AegisOps-owned lifecycle truth.

That means the first reviewed path may create a coordination ticket reference, but it must not make external status, assignee, queue, closure, SLA, or comment state authoritative for AegisOps decisions.

## 3. Reviewed Outbound Payload

The reviewed contract is intentionally narrow. At minimum, the outbound create contract must preserve and bind:

| Field | Required meaning for the first reviewed path |
| ---- | ---- |
| `case_id` | Required authoritative AegisOps case anchor for the coordination action. |
| `coordination_reference_id` | Required immutable AegisOps coordination-link identifier for the reviewed outbound create attempt. |
| `coordination_target_type` | Required reviewed target family, constrained to the reviewed coordination substrate or reviewed fallback. |
| `requested_payload` | Required reviewed coordination-ticket create payload or reviewed payload reference that approval covers exactly. |
| `payload_hash` | Required integrity value that binds approval, delegation, receipt, and reconciliation to the same reviewed create payload. |
| `idempotency_key` | Required replay-safe key for the exact approved create intent. |
| `external_receipt_id` | Required downstream receipt identifier once the reviewed target accepts the create request. |

The first reviewed payload may include only the coordination content needed to open and later inspect one external coordination ticket under explicit AegisOps control.

Allowed outbound content is limited to the reviewed coordination target selection, reviewed operator-visible summary and description content for the coordination ticket, reviewed severity or routing hints that remain subordinate to AegisOps truth, and the explicit AegisOps linkage values needed for later receipt binding and reconciliation.

The first reviewed payload must not export approval outcomes as downstream-owned truth, must not export mutable case lifecycle as if the ticket now owns it, and must not rely on free text alone for the authoritative linkage back to AegisOps.

## 4. Idempotency, Receipt, and Reconciliation Contract

The downstream receipt must prove which reviewed coordination target accepted which bounded create request.

At minimum, the downstream receipt must remain bindable to the reviewed `case_id`, `coordination_reference_id`, `coordination_target_type`, `payload_hash`, and `idempotency_key`, plus the reviewed downstream ticket identifier and operator-visible link returned by the target.

The receipt is sufficient only for proving that a reviewed coordination target accepted or rejected one reviewed create request. It is not sufficient to prove case closure, approval satisfaction, execution success, or reconciliation completion.

If the downstream target cannot prove whether a duplicate create request matches the same approved intent, AegisOps must fail closed and preserve the result as an explicit reconciliation concern instead of inferring safe deduplication.

If a create attempt returns a receipt that cannot be bound back to the approved `case_id`, `coordination_reference_id`, `coordination_target_type`, `payload_hash`, and `idempotency_key`, AegisOps must reject the result as authoritative evidence for the reviewed create path and keep the mismatch visible.

If a reviewed create attempt is rejected, times out, expires, or returns an ambiguous duplicate outcome, the control plane must preserve the authoritative AegisOps state chain and record the unresolved downstream outcome explicitly rather than implying success from partial downstream activity.

A failed, rejected, expired, or unbound create attempt must not leave durable partial truth behind inside AegisOps.

Rollback posture for the first reviewed path is conservative: do not invent downstream success, do not auto-close or auto-delete on ambiguous outcomes, and require explicit operator follow-up whenever the reviewed receipt cannot prove one clean create result for one approved intent.

## 5. Approval and Policy Posture

Human approval is required for the first reviewed `create_tracking_ticket` path.

The approval must remain bound to one bounded create request, one reviewed coordination target, one reviewed payload hash, one reviewed idempotency key, and one authoritative `case_id`.

No policy shortcut is approved in this phase for inferring that a ticket create is safe because it looks reversible, because a downstream operator asked for it in free text, or because a similar create happened previously.

If provenance, target scope, approval context, or target-family binding is missing, malformed, or only partially trusted, the create path must fail closed rather than guessing the missing context.

## 6. Explicit Out of Scope

This contract does not approve status synchronization, close or reopen delegation, comment synchronization, downstream case ownership, or downstream approval authority.

It also does not approve ticket-driven case creation, downstream truth selection based on queue or assignee state, background polling as lifecycle authority, or any broadened write path beyond one reviewed create-ticket delegation path.

The first reviewed contract is intentionally limited to outbound coordination-ticket creation plus explicit receipt and reconciliation handling so later phases cannot smuggle in bidirectional truth or broad lifecycle control under the same label.

## 7. Baseline Alignment Notes

This contract keeps the first reviewed ticket create path aligned with the existing response-action safety model and the control-plane reconciliation model by treating the outbound create as a bounded `Soft Write`, preserving AegisOps-owned authority, and rejecting ambiguous or partially trusted receipt state.

It leaves broader synchronization, closure, reopen, comment, and downstream authority questions out of scope until a later reviewed issue defines them explicitly and proves they do not weaken the current authority boundary.
