# AegisOps Response Action Safety and Approval Binding Model

## 1. Purpose

This document defines the baseline safety model and approval binding requirements for future AegisOps response actions.

It supplements `docs/requirements-baseline.md` and `docs/secops-domain-model.md` by making approval-gated response expectations specific enough to review, audit, and verify before any live workflow implementation exists.

This document defines policy and evidence requirements only. It does not introduce live workflows, approval-exempt write paths, or autonomous response behavior.

## 2. Action Safety Classes

Action classes define the minimum approval and evidence posture required before execution may proceed.

| Class | Meaning | Minimum expectation |
| ---- | ---- | ---- |
| `Read` | Collect, inspect, validate, or simulate state without changing the target system. | Request context and execution logging are still required, but approval may be policy-driven instead of human-gated when the action remains strictly non-mutating. |
| `Notify` | Send operator-facing or stakeholder-facing communication without changing the protected target itself. | The request must identify recipients, message intent, and escalation path so notification does not become an unreviewed indirect write against the wrong audience. |
| `Soft Write` | Change workflow, coordination, quarantine, ticketing, or other reversible control state with bounded impact. | Human approval is required unless an approved future policy narrowly authorizes the exact action pattern and records equivalent evidence. |
| `Hard Write` | Change production or security-relevant target state with material operational effect, including disablement, deletion, credential impact, or infrastructure mutation. | Explicit human approval, strong binding evidence, rollback or containment planning, and post-action verification are mandatory. |

Class assignment must be conservative. If an action could plausibly change protected target state or operator trust state, it must not be classified as `Read`.

## 3. Minimum Action Request Fields

Every action request must identify the requester, the intended action class, the target, the justification, and the exact payload or payload reference proposed for execution.

At minimum, an action request must record:

| Field | Required binding purpose |
| ---- | ---- |
| `action_request_id` | Provides the immutable control-plane identifier for the exact request under review and execution binding. |
| Request identifier | Distinguishes one requested action from later edits, retries, or related cases. |
| Requester identity | Binds the proposed action to the accountable human or approved service principal that asked for it. |
| Linked case, alert, finding, or incident reference | Preserves the investigative context that justified the request. |
| Action class | Determines the minimum approval, dry-run, rollback, and verification expectations. |
| Target type and target identifier | Makes the affected host, account, workflow object, recipient set, or other target specific enough to review. |
| Target snapshot or version reference | Captures the reviewed target state that approval covers. |
| Requested payload or payload reference | Prevents approval from floating across materially different commands, parameters, or templates. |
| Payload hash | Gives execution a stable integrity check against the approved payload. |
| Requested authority and rationale | States why the action is needed and what authority boundary it expects to cross. |
| Approval requirement and quorum rule | Declares whether the action needs one approver, multiple approvers, or another explicit approval policy outcome. |
| Expiry timestamp | Prevents stale approval from being replayed against later conditions. |
| Dry-run requirement | States whether reviewed dry-run evidence is mandatory before execution. |
| Rollback or containment expectation | Records the expected reversal or containment posture for write actions. |
| Verification plan | Defines what evidence must be collected after execution to prove the intended effect. |

Execution must not proceed when the action request lacks target specificity, approval requirements, expiry, or the evidence needed to bind approval context to execution context.

A generic "run containment" or "approve action" request is insufficient. The request must be precise enough that a reviewer can tell exactly who asked for what action, against which target snapshot, with which payload, under which time bound.

## 4. Approval Binding Requirements

Approval decisions must remain separate from execution attempts.

An approval decision answers whether a specific action request is authorized under policy. It does not prove that the action was attempted, and execution metadata must not be used as a substitute for the approval record.

The approval record must bind the requester identity, approver identity, target snapshot, payload hash, approval timestamp, expiry, and required quorum result to the specific action request.

Each approval decision must also carry an immutable `approval_decision_id` so approval outcome does not get inferred from workflow history or overwritten by later review activity.

The approval record must also capture the approval outcome, the approver rationale or conditions, and any execution constraints that narrow what may happen after approval.

If dry-run evidence is required for the action class, the approval record must reference the reviewed dry-run result that matches the approved target snapshot and payload hash.

If quorum is required, each participating approver must be individually attributable, and the final approval state must record whether the quorum was satisfied before expiry.

Execution must perform post-approval drift checks before acting.

At minimum, drift checks must compare the current requester identity, target snapshot, payload hash, approval status, expiry, quorum result, and dry-run evidence against the approved record before any downstream write occurs.

An execution attempt must be rejected when requester identity, target snapshot, payload hash, expiry, quorum, or required dry-run evidence no longer matches the approved record.

Approval reuse is prohibited across materially different targets, payloads, or time windows even if the operator intent appears similar. A new action request and approval decision are required when the reviewed context changes.

At minimum, the action-request lifecycle must distinguish `draft`, `pending_approval`, `approved`, `rejected`, `expired`, `canceled`, `superseded`, `executing`, `completed`, `failed`, and `unresolved`, while the approval-decision lifecycle must distinguish `pending`, `approved`, `rejected`, `expired`, `canceled`, and `superseded`.

## 5. Execution Safeguards

Every execution attempt must carry an idempotency key that is unique for the approved action request and execution intent.

The idempotency key must let the execution layer distinguish first execution from retried delivery, duplicate trigger, or replay attempt without treating those paths as fresh approvals.

Execution records must capture the downstream result, verification evidence, and rollback or containment outcome where applicable.

Duplicate execution attempts for the same approved action request must be prevented unless an explicitly recorded retry policy allows another attempt under the same binding context.

Allowed retries must remain tied to the same approved request, payload hash, target snapshot, and expiry window. A retry must not silently widen target scope or change the action payload.

Write-capable actions must record rollback expectations before execution and must record whether rollback, compensation, or explicit containment guidance was used after any partial or failed execution.

Post-action verification must confirm the expected target state or clearly record the residual risk and operator follow-up required.

If verification fails or remains inconclusive, the execution record must preserve that outcome explicitly rather than implying success from approval or workflow completion alone.

## 6. Baseline Alignment Notes

This model preserves the baseline separation between detection, approval, and execution and prevents approval from degrading into a generic approve button.

It reinforces the requirements baseline rule that destructive or high-impact actions require approval, that executed actions must be logged, that dry-run behavior should exist where applicable, and that write actions need rollback or containment guidance.

It also keeps `Action Request`, `Approval Decision`, and `Action Execution` aligned with the domain-model boundaries already defined in `docs/secops-domain-model.md`.
