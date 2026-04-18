# AegisOps Phase 26 First Coordination Substrate and Non-Authoritative Ticket Boundary

## 1. Purpose

This document selects the first reviewed coordination substrate for Phase 26 and defines the non-authoritative boundary that keeps AegisOps in control of policy-sensitive workflow truth.

It supplements `docs/requirements-baseline.md`, `docs/response-action-safety-model.md`, and `docs/control-plane-state-model.md` by naming one reviewed coordination target and by bounding how ticket references and future coordination soft writes may appear without redefining case authority, approval authority, execution authority, or reconciliation authority.

This document defines reviewed design scope only. It does not approve live ticket-system provisioning, background synchronization, bidirectional case management, or approval-by-ticket behavior.

## 2. Reviewed Selection

Zammad is the preferred first reviewed coordination substrate for Phase 26.

GLPI remains the reviewed fallback only if Zammad proves unsuitable under later implementation review, deployment fit, or contract review.

The reviewed choice is intentionally narrow. Phase 26 does not approve a broad ticketing abstraction layer, a generalized ITSM migration program, or multiple equally authoritative coordination systems.

## 3. Authority Boundary

The selected coordination substrate is a non-authoritative coordination target.

AegisOps remains authoritative for alert, case, approval, execution, and reconciliation truth.

That means ticket state must not become case truth, ticket approval state must not become approval truth, and downstream coordination activity must not become execution truth or reconciliation truth.

External queue moves, assignee changes, comments, SLA state, workflow status, or closure flags may be recorded as coordination context, but they remain subordinate evidence rather than lifecycle authority.

If a coordination substrate and the AegisOps control-plane record disagree, the AegisOps-owned record remains authoritative and the disagreement must remain visible for operator review.

## 4. Reviewed Capability Slice

The approved Phase 26 slice is limited to a link-first ticket reference plus one future reviewed create-ticket soft-write path.

The link-first ticket reference path allows operators to attach and inspect a reviewed external ticket pointer without asking the external system to own the case lifecycle.

The future reviewed create-ticket soft-write path is limited to opening a coordination ticket under explicit AegisOps control once later issues define the exact action request, approval posture, delegation contract, and validation coverage.

This slice does not approve ticket-driven case creation, ticket-driven approval, ticket-driven execution dispatch, background ticket polling as truth selection, or automatic case closure from external ticket events.

## 5. Minimum Reviewed Identifiers and Receipts

The reviewed Phase 26 coordination boundary must preserve explicit AegisOps-owned linkage fields rather than relying on free text or operator memory.

At minimum, the reviewed design expects:

- `coordination_reference_id` as the immutable AegisOps identifier for one reviewed external coordination link;
- `coordination_target_type` to declare the reviewed substrate family, such as `zammad`;
- `coordination_target_id` for the durable external ticket identifier returned by the reviewed target;
- `ticket_reference_url` for the operator-visible external ticket link;
- `external_receipt_id` for any reviewed downstream receipt returned by a future create-ticket path;
- `delegation_id` when a future approved create-ticket soft write is delegated through a reviewed execution surface;
- the bound `case_id`, and later any linked `action_request_id` or `approval_decision_id`, so the coordination record stays anchored to the authoritative control-plane record chain.

These identifiers and receipts support operator-visible references, future contract design, delegation, and validation without promoting the external ticket system into the source of truth.

## 6. Fail-Closed Expectations

The reviewed coordination path must fail closed when the authoritative AegisOps case anchor is missing, when the requested target substrate is not the reviewed coordination substrate or reviewed fallback, or when an external receipt cannot be bound back to the explicit AegisOps linkage fields.

Missing ticket links, stale coordination URLs, or absent downstream receipts must remain visible as coordination gaps. They must not be interpreted as proof that no case exists, that approval happened elsewhere, or that execution and reconciliation completed successfully.

Operator convenience does not justify inferring authority from whichever ticket status or comment was updated last.

## 7. Downstream Follow-On Scope

This decision is intended to unblock later issues that define:

- the exact link-only coordination-reference record shape;
- the future reviewed create-ticket contract and soft-write delegation boundary;
- operator review surfaces that display external coordination state without treating it as case truth; and
- validation coverage that proves ticket-side drift cannot silently overwrite AegisOps-owned records.
