# AegisOps Business-Hours SecOps Daily Operating Model

## 1. Purpose

This document defines the business-hours SecOps daily operating model for the AegisOps baseline.

It supplements `docs/requirements-baseline.md`, `docs/secops-domain-model.md`, `docs/auth-baseline.md`, `docs/response-action-safety-model.md`, and `docs/runbook.md` by defining the analyst-facing review flow that future UI, workflow, and runbook work must support.

This document defines operating expectations, records, and decision points only. It does not create runtime automation, commit AegisOps to specific staffing levels, or authorize destructive response without the separately approved approval model.

## 2. Operating Assumptions

This model assumes business-hours analyst coverage rather than 24x7 staffed monitoring.

Finding or alert intake enters the analyst review queue for the next business-hours review cycle unless an explicitly defined escalation path applies.

The default daily model assumes analysts review queued findings and alerts during scheduled working hours, with explicit prioritization rather than continuous around-the-clock watchstanding.

Read-oriented enrichment, context collection, note-taking, and case updates may occur during business hours without separate approval as long as they do not cross into response execution or unauthorized changes.

Write-oriented, destructive, or externally visible response actions remain approval-bound under the baseline even when the analyst believes the action is urgent.

Business-hours operation does not mean low rigor. Analysts must still preserve record quality, escalation clarity, evidence capture, and auditability for every reviewed work item.

## 3. Daily Analyst Workflow

### 3.1 Intake and Queue Review

The analyst begins by validating whether the incoming finding or alert is in scope, duplicated, or obviously explained by known benign context.

Initial review should answer these questions before deeper investigation begins:

- Is the item a valid routed work item rather than ingestion noise or a duplicate?
- Does existing context already explain the activity as false positive, benign positive, expected administrative activity, duplicate, or accepted risk?
- Does the item require immediate same-day handling, business-hours follow-up, or explicit after-hours escalation?

If the item is clearly duplicated or otherwise already accounted for, the analyst closes or links it using the approved disposition and preserves the relationship to the existing alert or case.

### 3.2 Investigation and Case Decision

If the item requires investigation, the analyst collects read-oriented evidence, confirms affected assets or identities, reviews related findings, and documents the working hypothesis.

A case is created when the work requires durable ownership, evidence capture, approval tracking, cross-shift visibility, or coordinated follow-up beyond the alert record itself.

The alert may remain the only work record when review is self-contained, no approval-bound action is needed, and closure can be justified directly on the alert.

When a case is opened, the analyst records at minimum:

- current owner;
- linked findings or alerts;
- relevant assets, identities, and evidence;
- current hypothesis and risk summary; and
- next review or follow-up expectation.

### 3.3 Recommendation and Approval Preparation

If the analyst concludes that a response step may be required, the analyst defines the recommended action without executing it.

The analyst records the recommended action, target scope, justification, and required approver before any approval-bound response is requested.

The recommendation should also state:

- why the action is needed;
- what evidence supports the recommendation;
- what could go wrong if the action is delayed or denied; and
- whether the action remains valid if approval arrives after the current review window.

### 3.4 Approval Outcome and Closure

If approval is granted and the workflow path is available, execution proceeds through the approved execution path and the resulting execution state is recorded separately from the approval outcome.

If approval is rejected, the analyst records the rejection outcome, updates the alert or case with the next planned step, and closes or re-routes the work according to the approver's decision and the remaining risk.

If no response action is required, the analyst closes the alert or case with the appropriate disposition, records the rationale, and captures any tuning or follow-up work that should be tracked outside the immediate review item.

Closure is not complete until the analyst can show what was reviewed, what was decided, what evidence was relied on, and whether any additional follow-up remains open.

## 4. Approval, Timeout, and Manual Fallback Expectations

Approval timeout must leave the action request in a non-executed state and force explicit analyst re-review during business hours before any later execution attempt.

Timeout is not silent approval, and timeout is not silent cancellation. It is a decision point that requires the next analyst review to determine whether the action is still necessary, still correctly scoped, and still justified by current evidence.

If the underlying facts changed while approval was pending, the prior request must be superseded or closed rather than reused without review.

Manual fallback may be used when the approved workflow path is unavailable, but the same approval decision, execution record, and post-action evidence requirements still apply.

Manual fallback is reserved for cases where an approved action must still be carried out but the normal orchestration path is impaired, unavailable, or unsuitable for the current boundary. It must not be used as a convenience path to bypass logging or policy controls.

When manual fallback is used, the operator must record:

- the original action request;
- the approval decision authorizing the action;
- why the standard workflow path was unavailable or inappropriate;
- who performed the fallback action;
- what was actually done; and
- what verification evidence confirmed the outcome.

## 5. After-Hours and Handoff Model

After hours, AegisOps does not imply an always-on analyst at the console.

After-hours handling must distinguish between work that can wait for the next business-hours review window and work that requires explicit escalation to an on-call or separately designated human owner.

Items that can safely wait remain queued for the next business-hours review cycle with enough context recorded that the next analyst does not need to reconstruct intent from raw system outputs alone.

Items that cannot safely wait require an explicit escalation decision. That decision must identify who is being contacted, why waiting until the next business-hours window is not acceptable, and what authority boundary applies if a response action may be required.

Approved escalation paths may notify or wake a designated human owner, but they do not convert the platform into a 24x7 staffed SOC and do not authorize autonomous destructive response.

Business-hours handoff must preserve queue state, open cases, pending approvals, expired approvals, and follow-up tasks so the next analyst can continue without reconstructing context from raw system logs.

At minimum, handoff notes should identify:

- which alerts or cases remain open;
- which actions are waiting for approval, have expired, or were rejected;
- which items were escalated after hours and to whom;
- what evidence or links the next analyst must review first; and
- what follow-up deadlines or business constraints still apply.

## 6. Required Records and Decision Points

The operating model depends on durable records that separate analytic intake, investigation, approval, execution, and closure.

| Record | What future implementation must preserve | Key decision point |
| ---- | ---- | ---- |
| `Alert or Finding Record` | Intake source, triage state, analyst-visible context, severity, and links to related records. | Does the item need analyst attention, deduplication, closure, or escalation? |
| `Case Record` | Durable ownership, evidence references, investigative notes, linked alerts, and follow-up tasks. | Does this work need a separate investigation record or can it remain inside the alert lifecycle? |
| `Approval Decision Record` | Approver identity, action scope, approval outcome, time of decision, and any conditions or constraints. | Was the requested action approved, rejected, or allowed to expire? |
| `Action Execution Record` | Execution path, executor identity, attempt/result state, target scope, and post-action verification evidence. | Did the action actually run, and if so, what happened? |
| `Closure or Disposition Record` | Final outcome, rationale, tuning implications, remaining accepted risk, and any downstream follow-up reference. | Is the work item ready to close, and what should future reviewers learn from the outcome? |

Future UI and workflow work must preserve, at minimum, these decision points:

- intake triage versus duplicate or immediate closure;
- alert-only handling versus case creation;
- recommendation-only state versus approval request;
- approved versus rejected versus expired approval outcome;
- automated execution versus manual fallback execution; and
- closure with clear rationale versus continued follow-up.

## 7. Baseline Alignment Notes

This operating model remains aligned to the baseline assumption that AegisOps supports business-hours-oriented security operations rather than a permanently staffed SOC.

It preserves the requirement that approval-sensitive actions remain human-gated, keeps approval and execution as separate records, and treats manual fallback as an exception path that still preserves auditability.

No part of this operating model creates a 24x7 staffing promise, an automatic destructive-action path, or a dependency on unsupported live-response coverage.
