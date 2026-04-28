# AegisOps Phase 45 Daily SOC Queue and Operator UX Hardening Boundary

## 1. Purpose

This document defines the reviewed Phase 45 daily SOC queue and operator UX hardening boundary.

It retroactively closes the Phase 45 contract around queue priority projection, mismatch and degraded lanes, alert, case, provenance, and action-review drilldowns, operator training alignment, and structured stale receipt status.

It supplements `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md`, `docs/phase-31-product-grade-hardening-boundary.md`, `docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md`, `docs/deployment/operator-training-handoff-packet.md`, `docs/deployment/pilot-readiness-checklist.md`, `docs/runbook.md`, and `docs/architecture.md`.

This document describes the closed Phase 45 daily queue and operator UX contract only. It does not change operator behavior, backend lifecycle behavior, queue lane behavior, approval behavior, execution behavior, reconciliation behavior, UI workflow authority, or deployment posture.

## 2. In Scope

Phase 45 closes one narrow daily SOC queue and operator UX hardening contract:

- the backend-derived analyst queue remains the reviewed daily work-selection projection for business-hours SOC review;
- queue priority projection stays derived from AegisOps alert, case, evidence, action-review, and reconciliation records rather than browser state or external substrate ordering;
- mismatch and degraded lanes stay visible as explicit review cues for reconciliation mismatch, stale receipt, optional-extension degradation, action-required work, and clean records;
- alert, case, provenance, and action-review drilldowns remain linked inspection surfaces anchored to explicit AegisOps record identifiers;
- operator training alignment keeps daily queue review, reviewed record chain explanation, non-authority rules, and evidence handoff language consistent with the product surface; and
- structured stale receipt status closes the wording-based lane risk by selecting the stale receipt lane from `lifecycle_state` and `ingest_disposition` fields instead of summary prose.

The Phase 45 boundary is a read and review closure. It records that the daily SOC queue can be understood from repo-owned artifacts without promoting queue projection, drilldown UI, stale receipt summary text, assistant output, optional-extension status, external tickets, or downstream receipts into workflow truth.

## 3. Out of Scope

Phase 45 does not authorize:

- new queue lane behavior;
- new operator UI workflows;
- new action types, approval paths, execution paths, or reconciliation outcomes;
- browser-owned queue priority, case lifecycle, approval, execution, reconciliation, or audit truth;
- treating optional-extension health, assistant output, external tickets, downstream receipts, or operator-readable summaries as control-plane authority;
- direct backend exposure or a new ingress path;
- production write-action expansion; or
- replacing the reviewed record chain with dashboard order, badge text, summary wording, nearby metadata, or naming conventions.

Operators and verifiers must use the reviewed queue and detail surfaces as subordinate read surfaces above AegisOps-owned records. They must not bypass the authoritative record chain to make a daily queue path appear complete.

## 4. Queue Priority Projection

The daily SOC queue projection is anchored in `control-plane/aegisops_control_plane/operator_inspection.py`.

The projection exposes read-only queue records from `inspect_analyst_queue()` and is surfaced through the protected `/inspect-analyst-queue` and `/operator/queue` paths.

The queue may include priority and selection context such as:

- `queue_selection`;
- `review_state`;
- `next_action`;
- `case_lifecycle_state`;
- `current_action_review`;
- `queue_lanes`;
- `queue_lane_details`;
- `substrate_detection_record_ids`;
- `accountable_source_identities`; and
- directly linked alert, case, evidence, action-request, approval, execution, and reconciliation identifiers.

These fields are operator-facing projection fields. They help operators decide where to inspect next, but they do not create or replace alert state, case state, approval state, execution state, reconciliation state, or audit truth.

When a queue projection conflicts with the underlying AegisOps records, the records remain authoritative and the projection must be repaired.

## 5. Mismatch and Degraded Lanes

The reviewed lane family remains explicit:

- `action_required`;
- `reconciliation_mismatch`;
- `stale_receipt`;
- `optional_extension_degraded`; and
- `clean`.

`reconciliation_mismatch` is selected from authoritative reconciliation lifecycle state and preserves mismatch summary detail for operator review.

`stale_receipt` is selected from structured stale receipt status. A reconciliation with `lifecycle_state == "stale"` or `ingest_disposition == "stale"` must render the stale receipt lane even when the human-readable summary changes. Summary text may explain the condition, but it must not be the lane selector.

`optional_extension_degraded` is subordinate optional context. It may tell the operator that optional supporting context is stale, delayed, or degraded, but it must not make optional extensions authority over mainline queue, case, approval, execution, reconciliation, or readiness truth.

`clean` means no reviewed lane condition is present in the projection. It does not mean the browser, ticket system, assistant, or downstream substrate independently closed the work.

## 6. Drilldown Surfaces

The reviewed drilldown surfaces are:

- `/inspect-alert-detail`;
- `/inspect-case-detail`;
- `/inspect-action-review`;
- the operator UI queue, alert detail, case detail, action-review detail, and provenance sections; and
- the CLI inspection commands that read the same control-plane records.

Drilldowns must stay anchored to explicit identifiers such as `alert_id`, `case_id`, `evidence_id`, `action_request_id`, `approval_decision_id`, `action_execution_id`, and `reconciliation_id`.

The alert, case, provenance, and action-review drilldowns may render subordinate source hints, ticket references, assistant citations, optional-extension status, execution receipts, and reconciliation summaries only as linked context under the reviewed AegisOps record chain.

They must fail closed or keep an explicit unresolved state when the selected record is missing, the selected identifier mismatches the response payload, the linked case or alert reference disagrees, the evidence provenance is absent, or the current action-review record cannot be tied back to the selected AegisOps anchor.

## 7. Operator Training Alignment

Operator training alignment is anchored in `docs/deployment/operator-training-handoff-packet.md` and verified by `scripts/verify-operator-training-handoff-packet.sh`.

Training must teach the same path rendered by the product surface:

`queue item -> alert or case detail -> evidence review -> casework update -> action-review read -> approval decision -> execution receipt -> reconciliation outcome -> evidence handoff`.

The training packet must keep external tickets, assistant output, optional evidence, downstream substrate receipts, browser state, and operator-readable summaries subordinate to the reviewed AegisOps record chain.

Daily queue review and drilldown practice must use repo-relative commands and placeholders. Training notes must not require workstation-local absolute paths or hidden manual steps.

## 8. Structured Stale Receipt Status

Structured stale receipt status is the Phase 45 closure for the earlier wording-based lane risk.

The stale receipt lane must be selected from durable reconciliation fields:

- `lifecycle_state`; and
- `ingest_disposition`.

The lane detail may include `summary` to explain the stale receipt to an operator, but summary wording is not authoritative and must not be parsed as the primary stale receipt signal.

If structured lifecycle or ingest disposition fields are missing, malformed, or inconsistent, the daily queue must preserve an explicit unresolved, degraded, or follow-up condition instead of guessing from nearby text.

## 9. Fail-Closed Conditions

Phase 45 must fail closed when any prerequisite record, provenance, scope, or boundary signal is missing, malformed, stale, mixed, or only partially trusted.

Blocking conditions include:

- queue records omit the explicit alert or case anchors required for the selected surface;
- queue priority projection is derived from browser order, external ticket priority, assistant output, optional-extension status, summary wording, or downstream substrate state instead of AegisOps records;
- mismatch and degraded lanes are hidden, merged into a generic warning, or treated as terminal success;
- stale receipt lane selection depends on human-readable summary text instead of `lifecycle_state` or `ingest_disposition`;
- alert, case, provenance, or action-review drilldowns accept missing or mismatched selected identifiers;
- operator-readable summaries are treated as authority rather than explanatory details;
- external ticket status, assistant output, optional-extension health, or downstream receipts override AegisOps lifecycle records;
- mixed snapshot reads stitch together queue, detail, evidence, action-review, and reconciliation records from incompatible moments in time without detecting the mismatch; or
- documentation, validation commands, or handoff notes introduce workstation-local absolute paths, hidden manual steps, or new production write behavior.

When one of these conditions appears, the correct outcome is rejection, blocked readiness, explicit degraded or unresolved state, or a documented follow-up. The system must not infer success from names, path shape, badge text, summary prose, external status, optional context, or nearby metadata.

## 10. Authority Boundary Notes

AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, approval, action intent, execution receipt, reconciliation, lifecycle, readiness, and audit truth.

The daily queue is a projection and work-selection surface, not a system of record.

The operator UI is a thin client and subordinate review surface, not a workflow authority.

daily SOC queue projection and drilldown UI do not become workflow truth.

operator-readable summaries are explanatory details, not authority.

Queue lanes, stale receipt summaries, optional-extension status, assistant notes, external tickets, downstream receipts, and operator-readable summaries are explanatory or supporting context only unless a reviewed AegisOps backend record explicitly binds them into the authoritative record chain.

## 11. Validation Expectations

Validation must remain documentation and boundary focused.

At minimum, validation should prove:

- the Phase 45 boundary and validation docs exist;
- the docs name in-scope, out-of-scope, fail-closed conditions, verifier references, and authority boundary notes;
- queue priority projection remains anchored to backend operator inspection and explicit AegisOps record identifiers;
- mismatch and degraded lanes remain explicit and non-authoritative;
- structured stale receipt status is selected from lifecycle and ingest disposition fields rather than summary wording;
- alert, case, provenance, and action-review drilldowns remain subordinate to selected authoritative records;
- operator training and pilot readiness references remain aligned; and
- no operator behavior, backend lifecycle behavior, or authority posture change is included.
