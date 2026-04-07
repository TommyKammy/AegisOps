# AegisOps SecOps Domain Model

## 1. Purpose

This document defines the first-class SecOps domain model for the AegisOps baseline.

It gives future implementation work a shared vocabulary for detection, investigation, approval, and response without collapsing those concerns into component-local meanings.

This document defines baseline semantics, ownership boundaries, and state transitions only. It does not introduce runtime behavior, workflow automation, or architecture changes.

For the reviewed Wazuh-specific intake boundary, see `docs/wazuh-alert-ingest-contract.md`.

For the reviewed downstream approval-bound delegation contract into automation substrates and executor surfaces, see `docs/automation-substrate-contract.md`.

## 2. Core Domain Objects

| Object | Definition |
| ---- | ---- |
| `Raw Event` | Source telemetry as received before AegisOps normalization or analytic shaping. |
| `Normalized Event` | Telemetry transformed into the approved event schema used by the analytics plane. |
| `Detection Rule` | Reviewed detection logic that evaluates normalized telemetry and declares matching conditions. |
| `Substrate Detection Record` | Vendor-native detection, correlation, or alerting record emitted by an approved upstream detection substrate before AegisOps admits or interprets it. |
| `Analytic Signal` | Vendor-neutral upstream SecOps primitive admitted by AegisOps from one or more substrate detection records and used to decide whether analyst-facing alert or case work should begin. |
| `Finding` | Detection result produced when reviewed detection logic matches relevant telemetry. A finding may be represented by a substrate detection record or preserved as source context for an analytic signal, but it is not the universal product primitive for all substrates. |
| `Hunt` | Analyst-directed exploration record created to test a threat hypothesis or investigate suspicious conditions beyond deterministic detection output. |
| `Hunt Hypothesis` | Explicit statement of what the analyst believes may be happening, why it is worth testing, and what evidence or observations would support or refute it. |
| `Hunt Run` | One bounded execution of a specific hunt hypothesis against a defined scope, time window, dataset, or query plan. |
| `Observation` | Recorded fact, pattern, or notable condition gathered during hunting or investigation that may inform later judgment but is not itself a deterministic detection claim. |
| `Lead` | Triage-worthy investigative signal derived from one or more observations, findings, or contextual facts that justifies additional analyst attention. |
| `Recommendation` | Proposed analyst or system action derived from findings, hunt conclusions, or AI-assisted interpretation that still requires human review within the appropriate approval boundary. |
| `AI Trace` | Preserved record of AI-assisted interpretation inputs, prompts, model outputs, confidence notes, and review context associated with a SecOps record. |
| `Correlation` | Explicit relationship that links related findings, alerts, cases, assets, or identities because they share meaningful operator-facing context. |
| `Alert` | Routed analyst-facing notification or queue item created from one or more findings that require attention. |
| `Case` | Investigation record that groups analyst work, related alerts, evidence, and response coordination for one work item. |
| `Incident` | Higher-order security event declaration used when one or more cases represent a material security event that needs coordinated handling. |
| `Asset` | Host, service, application, workload, network location, or other managed entity referenced during detection or response. |
| `Identity` | Human or machine principal associated with activity, ownership, access, or response authorization scope. |
| `Evidence` | Preserved supporting record used to explain, justify, or reconstruct SecOps decisions and conclusions. |
| `Action Request` | Proposed response step that describes the intended action, target scope, requested authority, and execution preconditions. |
| `Approval Decision` | Explicit approval outcome for a specific action request. |
| `Action Execution` | Record of the actual downstream attempt, progress, and result for an approved or explicitly allowed action request. |
| `Disposition` | Closure or outcome classification applied to a finding, alert, case, or incident by the owner of that specific record type. |

## 3. Relationship and State Boundaries

A `Raw Event` becomes a `Normalized Event` when the analytics plane has accepted and shaped it into the approved schema. Normalization does not imply a detection match.

A `Detection Rule` evaluates `Normalized Event` records. It does not own source telemetry, approvals, or action execution.

A `Substrate Detection Record` is the substrate-native detection, correlation, or alerting artifact emitted by an approved upstream detection substrate.

A substrate detection record preserves the substrate's own identifiers, timestamps, and local semantics. It must not be mistaken for an AegisOps alert, case, approval, or execution record.

An `Analytic Signal` is the vendor-neutral upstream SecOps primitive admitted by AegisOps from one or more substrate detection records.

An analytic signal preserves durable references back to the originating substrate detection records, but it remains distinct from both those substrate-native records and the downstream alert or case lifecycle that AegisOps may create from it.

For Wazuh-origin alerts, `docs/wazuh-alert-ingest-contract.md` defines the reviewed required fields, optional fields, provenance set, and mapping from the Wazuh-native alert into the admitted analytic-signal boundary.

A finding is the normalized analytic assertion that detection logic matched relevant telemetry.

A finding may supply analytic meaning to an analytic signal, but a finding does not replace the vendor-neutral analytic-signal boundary and is not interchangeable with an alert, case, or action execution.

A hunt is an analyst-directed exploration record created to test a threat hypothesis or investigate suspicious conditions beyond deterministic detection output.

A hunt hypothesis is the explicit statement of what the analyst believes may be happening, why it is worth testing, and what evidence or observations would support or refute it.

A hunt run is one bounded execution of a specific hunt hypothesis against a defined scope, time window, dataset, or query plan.

An observation is a recorded fact, pattern, or notable condition gathered during hunting or investigation that may inform later judgment but is not itself a deterministic detection claim.

An observation may support a finding or a lead, but it is not itself a finding because it does not assert that reviewed detection logic matched.

An observation may attach to a hunt run, alert, case, or stand-alone investigative thread, but attachment does not convert the observation into evidence custody, alert state, or case state.

A lead is a triage-worthy investigative signal derived from one or more observations, findings, or contextual facts that justifies additional analyst attention.

A lead may promote into alert or case work when triage determines the signal warrants tracked investigation, but the lead remains distinct from the alert or case record it informs.

The lead record remains the system of record for the pre-promotion hypothesis, triage rationale, and promotion decision. AI trace text, case notes, or alert notes may reference that decision, but they must not replace the lead record itself.

A recommendation is a proposed analyst or system action derived from findings, hunt conclusions, or AI-assisted interpretation that still requires human review within the appropriate approval boundary.

A recommendation may attach to a hunt, hunt run, lead, alert, or case, but it remains advisory context until an explicit downstream task, approval, or action-request record is created.

An AI trace is the preserved record of AI-assisted interpretation inputs, prompts, model outputs, confidence notes, and review context associated with a SecOps record.

An AI trace is not evidence. It preserves how AI-assisted interpretation was produced and reviewed, while evidence preserves the underlying supporting artifacts and chain of custody.

An AI trace may attach to a hunt, hunt run, observation, lead, recommendation, alert, or case, but it does not own the lifecycle of those records and must not become the implicit source of truth for promotion, approval, or closure.

AI-assisted interpretation may summarize, rank, or recommend, but it must not overwrite deterministic finding output, evidence custody, approval decisions, or action execution records.

Correlation is the explicit relationship that links related findings, alerts, cases, assets, or identities because they share meaningful operator-facing context.

An alert is the routed operator-facing notification or queue item created from one or more findings after baseline triage policy decides analyst attention is required.

A finding may exist without an alert. The finding remains the analytic result, while the alert is the decision to route that result into analyst attention.

A case is the investigation record that groups alerts, evidence, analyst notes, and response coordination for one work item.

An alert may exist without a case. A case begins only when investigation state must be tracked as its own record rather than inferred from alert status alone.

An incident is the higher-order security event declaration used when one or more cases represent a material security event that needs coordinated operational handling.

A case may exist without an incident. An incident is created only when separate investigative work must be coordinated as one security event.

`Asset` and `Identity` are reference entities. They contextualize findings, alerts, cases, incidents, evidence, and action requests, but they are not themselves detections or response outcomes.

`Evidence` is supporting material linked to another record. Evidence is not a substitute for alert state, case state, or incident state.

`Evidence` preserves source artifacts, provenance, and custody. AI interpretation may reference evidence, but it does not replace or mutate the underlying evidence record.

`Action Request` is the proposal to do something. It defines the requested response intent, target, justification, and required approval boundary.

An approval decision records whether a specific action request is authorized, rejected, or expired.

An `Approval Decision` is not execution. Approval answers whether an `Action Request` may proceed under policy; it does not prove that any downstream action was attempted or completed.

An action execution records the actual downstream attempt or completion state for an approved or explicitly allowed action request.

An `Action Execution` is not approval. Execution records what was attempted or completed in the execution plane after approval requirements were satisfied or an approved exception path allowed it.

The reviewed delegation contract for carrying approved payload, idempotency, expiry, provenance, and execution-surface identity into downstream execution is defined in `docs/automation-substrate-contract.md`.

`Disposition` is a classification outcome owned by the lifecycle of the record it closes. A finding disposition does not replace alert disposition, and a case disposition does not replace incident disposition.

Substrate detection records, analytic signals, workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states.

## 4. Baseline System of Record

| Object or boundary | Baseline system of record | Ownership note |
| ---- | ---- | ---- |
| `Raw Event` | OpenSearch ingestion and analytics plane | Raw telemetry lands and persists in the analytics plane before any higher-level SecOps interpretation. |
| `Normalized Event` | OpenSearch ingestion and analytics plane | The analytics plane owns normalized telemetry shape and analytic readiness. |
| `Detection Rule` | Sigma for reviewed source definition; OpenSearch for deployed runtime materialization | Sigma remains the reviewable rule-definition source, while OpenSearch owns the deployed detector representation used at runtime. |
| `Substrate Detection Record` | Approved upstream detection substrate | The substrate owns its native detection, correlation, or alerting record shape and identifier semantics before AegisOps admits them as upstream input. |
| `Analytic Signal` | AegisOps analytic-signal intake boundary referencing approved upstream detection substrates | The analytic signal is the vendor-neutral upstream product primitive for control-plane intake, while still preserving links to substrate-native records. |
| `Finding` | OpenSearch detection and analytics plane | A finding is an analytics-plane output and must not be redefined as workflow state. |
| `Hunt` | Future AegisOps hunt management control layer | Hunt lifecycle belongs to the analyst-directed exploration record and must remain separate from deterministic findings, alerts, and cases. |
| `Hunt Hypothesis` | Future AegisOps hunt management control layer | Hypothesis ownership stays with the hunt record family so the analytic question remains reviewable across multiple runs. |
| `Hunt Run` | Future AegisOps hunt management control layer | Each run records bounded execution context and outcome for one hypothesis evaluation without becoming the system of record for alerts or cases. |
| `Observation` | Future AegisOps hunt and investigation record layer | Observations preserve notable facts gathered during hunts or investigations without asserting a reviewed finding or opening case state on their own. |
| `Lead` | Future AegisOps triage and investigation control layer | Lead lifecycle captures triage-worthy investigative signals without collapsing directly into findings, alerts, or cases until an explicit promotion decision is made. |
| `Recommendation` | Future AegisOps analyst decision support control layer | Recommendations remain advisory outputs and must not become approvals, action requests, or executions by implication. |
| `AI Trace` | Future AegisOps AI interpretation record layer | AI trace ownership preserves how interpretation was generated and reviewed while keeping evidence custody and deterministic system records separate. |
| `Correlation` | Future AegisOps correlation and triage control layer | Correlation records operator-meaningful relationships without replacing the lifecycle of the linked records. |
| `Alert` | Future AegisOps alert routing and triage control layer | Alert lifecycle belongs to the future control layer that decides routing, deduplication, and analyst attention. |
| `Case` | Future AegisOps case management control layer | Case lifecycle must be owned separately from analytics outputs and workflow runs. |
| `Incident` | Future AegisOps incident command and coordination control layer | Incident lifecycle is the coordinated operational record above individual cases. |
| `Asset` | Future AegisOps asset context control layer | Asset identity and enrichment context must remain separate from event and workflow records. |
| `Identity` | Future AegisOps identity context control layer | Identity context links principals to activity and approvals without collapsing into alert or case state. |
| `Evidence` | Future AegisOps evidence control layer | Evidence custody and references belong to a distinct record family rather than workflow execution metadata. |
| `Action Request` | Future AegisOps response planning and approval control layer | The request is the authoritative statement of intended response scope before execution. |
| `Approval Decision` | Future AegisOps approval control layer | Approval state must remain distinct from both request definition and execution status. |
| `Action Execution` | Reviewed automation substrate or controlled executor surface | The reviewed execution surface owns execution attempts and completion records, but it does not own the approval verdict or reconciliation truth. |
| `Disposition` | The owner of the record being closed | Disposition belongs to the lifecycle authority of the finding, alert, case, or incident it classifies. |

## 5. Promotion and Correlation Rules

An analytic signal is the common upstream product primitive from which alert or case routing decisions begin.

An analytic signal promotes to an alert only when triage policy determines that analyst attention, tracking, notification, or downstream workflow handling is required.

Analytic-signal-to-alert routing must preserve the distinction between the substrate detection record, any admitted analytic signal, any finding or correlation claim preserved as source context, and the downstream alert record created for analyst work.

A substrate detection record identifier, an analytic signal identifier, and an alert identifier are related references, not interchangeable lifecycle keys.

A finding may remain source analytic context without becoming an alert when the result is retained only for analytics, threshold accumulation, tuning review, or later correlation and does not yet require direct operator handling.

A hunt may produce observations, leads, recommendations, or supporting context for findings, alerts, and cases, but hunt records do not replace those records.

A lead promotes to an alert only when triage decides the investigative signal requires durable analyst queueing or response handling.

A lead may be attached directly to an existing case when the signal materially advances an active investigation without requiring a separate alert lifecycle.

Lead promotion must preserve explicit linkage from the lead to the destination alert or case so future workflow and schema work can reconstruct why tracked investigation began without mining case notes or AI trace history.

Correlation links records by shared context, but it does not by itself create an alert, open a case, or declare an incident.

Correlation may connect records through common asset, identity, detection family, campaign hypothesis, time-bounded pattern, or other analyst-meaningful context, but it must not merge unrelated claims into a single lifecycle record without an explicit promotion decision.

An alert promotes to a case only when the operator needs a durable work record for investigation, evidence handling, ownership, or response coordination beyond the alert queue item itself.

An incident is declared only when one or more cases represent a material security event that requires coordinated operational handling beyond a single investigative work item.

## 6. Grouping, Deduplication, and Case Creation Expectations

A case must not be created for every alert by default.

Grouping means related findings may be collected under one alert when they express the same operator-facing claim closely enough that one analyst work item can review them coherently.

Deduplication means additional findings are attached to an existing alert or case when they restate the same analytic claim against materially the same operational target within the active review window.

When upstream analytics restate the same claim without materially changing analyst work, the control plane must update or link the existing alert rather than minting a new alert identifier.

A new alert must be created instead of deduplicating when severity, target scope, response owner, or review window changes enough that analyst handling would differ.

Grouping and deduplication must reduce alert volume without erasing accountability. The retained alert or case must still preserve references to the contributing findings and the rule used to collapse them.

A case is created when analyst work requires durable ownership, evidence collection, note-taking, handoff, or coordinated response beyond the alert record itself.

An alert may be closed without a case when the required analyst review fits inside the alert lifecycle and does not require broader investigation management.

## 7. Disposition and Closure Taxonomy

Closure disposition must classify both operational outcome and future tuning implications in reviewable terms.

The same label may appear across findings, alerts, cases, and incidents, but each record type owns its own disposition decision and rationale.

| Disposition | Meaning | Tuning implication |
| ---- | ---- | ---- |
| `False Positive` | The analytic claim was incorrect. | Detection logic, enrichment, or source mapping should be corrected or tightened. |
| `Benign Positive` | The activity occurred as detected but does not represent harmful or policy-violating behavior in context. | Detection scope, routing, or enrichment may need adjustment so expected benign activity is separated from true security work. |
| `Duplicate` | The record does not represent new work because another active or closed record already tracks the same claim. | Grouping and deduplication logic should preserve linkage and avoid repeated analyst work. |
| `Expected Administrative Activity` | The activity is legitimate administrative, maintenance, or approved operational work that should remain distinguishable from suspicious behavior. | Tuning should prefer explicit allowlisting, context enrichment, or operator guidance rather than treating the event as unexplained noise. |
| `Accepted Risk` | The activity or exposure is known and consciously accepted by the accountable owner, so no further investigative escalation is required under the current baseline. | Future alerts should retain the acceptance context and review horizon rather than reopening identical work without changed conditions. |

Disposition must not be used to hide unresolved ownership. If the operator cannot explain why a record is closed, the record is not ready for closure.

## 8. Baseline Alignment Notes

This baseline keeps detection, investigation, approval, and execution as separate first-class concerns.

It explicitly prevents substrate-native detection records or findings from being treated as if they were alerts, prevents n8n workflow state from becoming the case system of record, and prevents approval state from being inferred from execution metadata.

Future implementation may materialize additional control layers for alerts, cases, incidents, approvals, evidence, assets, and identities, but those runtime changes require separate approved work.
