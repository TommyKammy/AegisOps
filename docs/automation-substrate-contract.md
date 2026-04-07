# AegisOps Approved Automation Delegation Contract

## 1. Purpose

This document defines the reviewed contract for delegating approved AegisOps actions into external automation substrates and controlled executor surfaces.

It supplements `docs/secops-domain-model.md`, `docs/response-action-safety-model.md`, and `docs/control-plane-state-model.md` by making the approved handoff contract explicit before Phase 13 implementation work introduces live adapters or executor code.

This document defines delegation, binding, provenance, and reconciliation requirements only. It does not introduce adapter code, isolated-executor implementation, or CI expansion in this phase.

## 2. Control-Plane Authority Boundary

AegisOps remains the authority for `Action Request`, `Approval Decision`, evidence linkage, `Action Execution` correlation, and `Reconciliation` state even when a reviewed automation substrate or executor surface performs downstream work.

Neither an automation substrate nor an executor surface may mint, overwrite, or become the system of record for approval truth, action-request truth, evidence custody, or reconciliation truth.

Delegation is allowed only after AegisOps has a bounded `Action Request` and a still-valid `Approval Decision` whose binding fields exactly match the downstream execution intent.

The approval record must persist an immutable approved expiry value or equivalent approved time bound so delegation can reject post-approval expiry drift against the approved record rather than trusting only mutable request state.

Substrate-local queued jobs, workflow definitions, connector payload history, and executor-local run logs may provide downstream evidence, but they do not become the approval authority or the reconciliation authority for the approved action path.

## 3. Approved Delegation Contract

The reviewed delegation record is the control-plane handoff artifact that binds approved response intent to one reviewed downstream execution surface.

At minimum, the contract must preserve:

| Field | Required delegation meaning |
| ---- | ---- |
| `delegation_id` | Immutable AegisOps delegation record identifier for one approved handoff into an automation substrate or executor surface. |
| `action_request_id` | Required AegisOps identifier for the exact request whose approved intent is being delegated. |
| `approval_decision_id` | Required AegisOps identifier for the approval outcome that authorizes the delegated intent. |
| `execution_surface_type` | Required reviewed surface class, constrained to approved automation-substrate or executor categories rather than vendor-local workflow labels. |
| `execution_surface_id` | Required identifier for the specific reviewed automation substrate or executor surface receiving the handoff. |
| `approved_payload` | Required exact payload or payload reference that downstream execution must honor. |
| `payload_hash` | Required integrity value that binds approval, delegation, execution, and reconciliation to the same reviewed payload. |
| `idempotency_key` | Required replay-safe key for the exact approved execution intent. |
| `expires_at` | Required delegation expiry inherited from or tighter than the approved execution window. |
| Provenance set | Required requester, approver, delegation issuer, issuance timestamp, and related evidence references needed to reconstruct who authorized and emitted the handoff. |

The approved payload must remain bound to one `Action Request`, one approval context, one reviewed target scope, and one reviewed execution surface at the time of delegation.

A reused approval decision must not authorize a materially different payload, target set, execution surface, or expiry window.

If target state, target identity, requested payload, or execution-surface destination drifts after approval, the old delegation contract is no longer valid for execution.

## 4. Approval-Bound Execution Identity and Reconciliation

The downstream execution intent must preserve `action_request_id`, `approval_decision_id`, `delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, and `payload_hash` so later `Action Execution` and `Reconciliation` records can prove what was authorized and what actually ran.

Execution-surface receipts, vendor run identifiers, and step logs are downstream evidence inputs. They must not replace the AegisOps-owned `Action Execution` or `Reconciliation` records.

Each later `Action Execution` record must link back to the originating `Action Request`, the governing `Approval Decision`, the emitted `delegation_id`, and the downstream `execution_run_id` observed on the reviewed surface.

Each later `Reconciliation` record must preserve whether the observed downstream execution matched the approved payload, approved target scope, reviewed execution surface, idempotency key, and expiry window.

If the downstream surface reports a run without a matching approved delegation record, AegisOps must treat that result as a reconciliation exception rather than infer approval from execution.

If the downstream surface reports the wrong payload hash, wrong target scope, wrong execution surface, or missing idempotency key, AegisOps must preserve that mismatch as explicit reconciliation state instead of normalizing it away.

If a delegation expires before the reviewed surface starts execution, the run must not be treated as newly approved by virtue of still having a vendor-local queued job.

## 5. Idempotency, Expiry, and Retry Rules

The `idempotency_key` belongs to the approved execution intent, not to a vendor-local retry counter or queue implementation detail.

Duplicate delivery, replay, retried dispatch, or duplicate substrate triggers must remain correlated to the same approved delegation context rather than being interpreted as fresh approvals.

Retries are allowed only when the retry remains inside the same approved payload binding, target scope, execution surface, and expiry window.

A new approval path is required before retry when the payload hash, target snapshot, execution surface, or expiry window changes.

If the execution surface cannot prove whether a received duplicate is the same approved intent or a changed request, AegisOps must keep the result in explicit reconciliation exception state until an operator resolves it.

## 6. Baseline Alignment Notes

This contract aligns the approved handoff model to the shipped vendor-neutral execution-surface vocabulary rather than reintroducing substrate-local approval or reconciliation authority.

It keeps concrete Shuffle adapter code, isolated-executor implementation, and Phase 13 CI expansion out of scope for this baseline.

Future implementation issues may build adapters, service endpoints, persistence shapes, or executor integrations on top of this contract, but they must preserve AegisOps as the authority for approval, evidence linkage, `Action Execution` correlation, and `Reconciliation`.
