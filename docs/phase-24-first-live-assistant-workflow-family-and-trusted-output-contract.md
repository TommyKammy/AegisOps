# AegisOps Phase 24 First Live Assistant Workflow Family and Trusted Output Contract

## 1. Purpose

This document defines the first live assistant workflow family and the trusted output contract for that family.

It supplements `docs/Revised Phase23-29 Epic Roadmap.md`, `README.md`, `docs/phase-15-identity-grounded-analyst-assistant-boundary.md`, and `docs/control-plane-state-model.md` by narrowing the first operator-facing assistant loop to a reviewed, bounded, advisory-only workflow family.

This document defines reviewed workflow scope and trusted output rules only. It does not approve live assistant authority over approval, delegation, execution, reconciliation, or policy interpretation.

## 2. First Live Assistant Workflow Family

The first live assistant workflow family is a bounded reviewed summarization family.

It is intentionally limited to two narrow operator tasks:

- `queue triage summary`
- `case summary`

This first live assistant workflow family does not include next-step recommendation draft generation, approval suggestions, delegation suggestions, action execution instructions, or policy interpretation.

The assistant remains advisory-only.

The bounded family is small enough to review end-to-end because both tasks render from one reviewed record chain and return operator-facing summaries rather than authority-bearing decisions.

## 3. Reviewed Record Inputs

This section defines the reviewed record inputs for the first live assistant workflow family.

The workflow family may ground only on reviewed record inputs that already exist in the authoritative AegisOps control-plane chain.

### 3.1 Queue Triage Summary Inputs

`queue triage summary` may render only from reviewed records already linked to the queued item:

- `Alert`
- `Case`, when one already exists for the queued alert
- linked `Evidence`
- linked `Observation` or `Lead`, when already reviewed
- linked `Recommendation`, only as cited context and not as live recommendation generation authority
- linked `Analytic Signal` or `substrate_detection_record_id`, only when already attached to a reviewed record

### 3.2 Case Summary Inputs

`case summary` may render only from reviewed records already linked to the case:

- `Case`
- linked `Alert`
- linked `Evidence`
- linked `Observation`
- linked `Lead`
- linked `Recommendation`
- linked `Action Request`, `Approval Decision`, `Action Execution`, and `Reconciliation`, when those records already exist on the reviewed case chain

The workflow family must prefer reviewed records and linked evidence over substrate-local summaries, analytics rows, or prompt-provided narrative.

If a requested summary cannot be grounded in reviewed record inputs, the workflow must force `unresolved`.

## 4. Workflow Task Boundaries

`queue triage summary` is the skim surface for the current queue item. It may summarize reviewed severity, reviewed state, linked evidence posture, and visible unresolved gaps for the next human reviewer.

`case summary` is the durable coordination surface for the current case. It may summarize reviewed scope, linked evidence, current lifecycle state, already-recorded recommendation context, and any already-recorded approval or reconciliation state.

Neither task may create a new recommendation, interpret policy, approve a request, delegate a request, execute an action, or resolve a reconciliation mismatch.

If the operator request asks for approval, delegation, execution, or policy interpretation, the assistant must force `unresolved` instead of returning a weak answer.

## 5. Trusted Output Contract

The trusted output contract for this workflow family is intentionally narrow and only allows summary-shaped fields.

Allowed fields:

The trusted output contract explicitly defines the allowed fields for this family and no other summary fields are permitted.

| Field | Rule |
| --- | --- |
| `workflow_family` | Must be `first_live_assistant_summary_family`. |
| `workflow_task` | Must be either `queue_triage_summary` or `case_summary`. |
| `status` | Must be `ready` or `unresolved`. |
| `summary` | A concise reviewed summary with no authority-bearing language. |
| `citations` | Required citations for every material claim in `summary`. |
| `unresolved_reasons` | Required when `status` is `unresolved`. |
| `operator_follow_up` | Optional next review prompt for the human operator, framed as review work rather than action authority. |

No additional fields are allowed for the first live workflow family.

The contract must not include approval decisions, delegation instructions, execution commands, policy conclusions, free-form tool requests, or hidden confidence fields.

## 6. Required Citation Fields

This section defines the required citation fields for the trusted output contract.

The `citations` field is required for every material claim and each citation entry must preserve the reviewed record chain.

Required citation fields:

| Citation field | Minimum rule |
| --- | --- |
| `record_family` | The reviewed source family such as `Alert`, `Case`, `Evidence`, `Recommendation`, or `Reconciliation`. |
| `record_id` | The stable reviewed identifier for the cited record. |
| `claim` | The specific supported claim or observation tied to that record. |
| `evidence_id` | Required when the claim depends on linked evidence rather than only the parent record state. |
| `reviewed_context_field` | Required when the claim depends on an explicit reviewed context identifier or lifecycle field. |

The trusted output contract must keep citations explicit enough that a reviewer can trace each claim back to reviewed record inputs without consulting hidden prompt state.

If required citations are missing, the workflow must force `unresolved`.

## 7. Unresolved Conditions

The workflow family must fail closed.

Trust-blocking conditions that must force `unresolved` include:

- If required citations are missing.
- If reviewed records conflict on lifecycle state, ownership, scope, or evidence-backed facts.
- If linked evidence is referenced in the summary but the corresponding reviewed `evidence_id` is absent.
- If the operator request asks for approval, delegation, execution, or policy interpretation.
- If the request depends on prompt-only facts, substrate-local summaries, or uncited analyst narrative that is not already preserved as reviewed record input.
- If the requested answer would require the assistant to collapse identity ambiguity or choose between conflicting reviewed records.

`unresolved_reasons` must name the blocking condition directly instead of softening it into a weak or speculative answer.

## 8. Authority Boundary

The assistant remains advisory-only for the first live assistant workflow family.

Approval, delegation, execution, and policy authority outside the assistant boundary must remain on the reviewed human and control-plane path.

This preserves approval, delegation, execution, and policy authority outside the assistant boundary.

The workflow family may summarize reviewed state, but it must not become approval authority, delegation authority, execution authority, reconciliation authority, or policy authority.

The trusted output contract exists to preserve operator review, not to create a new authority surface.

## 9. Live Rollout Non-Expansion Rules

This first live assistant workflow family does not authorize:

- next-step recommendation draft generation as a live workflow;
- approval recommendation or approval routing authority;
- delegation or execution proposal payload construction;
- policy interpretation or policy exception handling;
- broad search-driven assistance outside the reviewed record chain; or
- any workflow family with more than the two narrow tasks listed in this document.

Future expansion must be reviewed as a separate workflow-family decision rather than inferred from this contract.

## 10. Alignment Notes

This Phase 24 workflow contract stays aligned with `docs/Revised Phase23-29 Epic Roadmap.md` by preferring a small business-hours operator loop over broad AI surface growth.

It stays aligned with `README.md` by keeping the assistant downstream of reviewed records and advisory-only.

It stays aligned with `docs/phase-15-identity-grounded-analyst-assistant-boundary.md` by preserving reviewed grounding, explicit citations, and fail-closed unresolved handling.

It stays aligned with `docs/control-plane-state-model.md` by keeping authoritative workflow truth on the AegisOps record chain rather than on assistant output.
