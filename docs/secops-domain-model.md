# AegisOps SecOps Domain Model

## 1. Purpose

This document defines the first-class SecOps domain model for the AegisOps baseline.

It gives future implementation work a shared vocabulary for detection, investigation, approval, and response without collapsing those concerns into component-local meanings.

This document defines baseline semantics, ownership boundaries, and state transitions only. It does not introduce runtime behavior, workflow automation, or architecture changes.

## 2. Core Domain Objects

| Object | Definition |
| ---- | ---- |
| `Raw Event` | Source telemetry as received before AegisOps normalization or analytic shaping. |
| `Normalized Event` | Telemetry transformed into the approved event schema used by the analytics plane. |
| `Detection Rule` | Reviewed detection logic that evaluates normalized telemetry and declares matching conditions. |
| `Finding` | Detection result produced when a detection rule matches relevant telemetry. |
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

A finding is the normalized analytic assertion that detection logic matched relevant telemetry.

An alert is the routed operator-facing notification or queue item created from one or more findings after baseline triage policy decides analyst attention is required.

A finding may exist without an alert. The finding remains the analytic result, while the alert is the decision to route that result into analyst attention.

A case is the investigation record that groups alerts, evidence, analyst notes, and response coordination for one work item.

An alert may exist without a case. A case begins only when investigation state must be tracked as its own record rather than inferred from alert status alone.

An incident is the higher-order security event declaration used when one or more cases represent a material security event that needs coordinated operational handling.

A case may exist without an incident. An incident is created only when separate investigative work must be coordinated as one security event.

`Asset` and `Identity` are reference entities. They contextualize findings, alerts, cases, incidents, evidence, and action requests, but they are not themselves detections or response outcomes.

`Evidence` is supporting material linked to another record. Evidence is not a substitute for alert state, case state, or incident state.

`Action Request` is the proposal to do something. It defines the requested response intent, target, justification, and required approval boundary.

An approval decision records whether a specific action request is authorized, rejected, or expired.

An `Approval Decision` is not execution. Approval answers whether an `Action Request` may proceed under policy; it does not prove that any downstream action was attempted or completed.

An action execution records the actual downstream attempt or completion state for an approved or explicitly allowed action request.

An `Action Execution` is not approval. Execution records what was attempted or completed in the execution plane after approval requirements were satisfied or an approved exception path allowed it.

`Disposition` is a classification outcome owned by the lifecycle of the record it closes. A finding disposition does not replace alert disposition, and a case disposition does not replace incident disposition.

OpenSearch findings, n8n workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states.

## 4. Baseline System of Record

| Object or boundary | Baseline system of record | Ownership note |
| ---- | ---- | ---- |
| `Raw Event` | OpenSearch ingestion and analytics plane | Raw telemetry lands and persists in the analytics plane before any higher-level SecOps interpretation. |
| `Normalized Event` | OpenSearch ingestion and analytics plane | The analytics plane owns normalized telemetry shape and analytic readiness. |
| `Detection Rule` | Sigma for reviewed source definition; OpenSearch for deployed runtime materialization | Sigma remains the reviewable rule-definition source, while OpenSearch owns the deployed detector representation used at runtime. |
| `Finding` | OpenSearch detection and analytics plane | A finding is an analytics-plane output and must not be redefined as workflow state. |
| `Alert` | Future AegisOps alert routing and triage control layer | Alert lifecycle belongs to the future control layer that decides routing, deduplication, and analyst attention. |
| `Case` | Future AegisOps case management control layer | Case lifecycle must be owned separately from analytics outputs and workflow runs. |
| `Incident` | Future AegisOps incident command and coordination control layer | Incident lifecycle is the coordinated operational record above individual cases. |
| `Asset` | Future AegisOps asset context control layer | Asset identity and enrichment context must remain separate from event and workflow records. |
| `Identity` | Future AegisOps identity context control layer | Identity context links principals to activity and approvals without collapsing into alert or case state. |
| `Evidence` | Future AegisOps evidence control layer | Evidence custody and references belong to a distinct record family rather than workflow execution metadata. |
| `Action Request` | Future AegisOps response planning and approval control layer | The request is the authoritative statement of intended response scope before execution. |
| `Approval Decision` | Future AegisOps approval control layer | Approval state must remain distinct from both request definition and execution status. |
| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state | n8n and its workflow state store own execution attempts and completion records, not the approval verdict. |
| `Disposition` | The owner of the record being closed | Disposition belongs to the lifecycle authority of the finding, alert, case, or incident it classifies. |

## 5. Baseline Alignment Notes

This baseline keeps detection, investigation, approval, and execution as separate first-class concerns.

It explicitly prevents OpenSearch findings from being treated as if they were alerts, prevents n8n workflow state from becoming the case system of record, and prevents approval state from being inferred from execution metadata.

Future implementation may materialize additional control layers for alerts, cases, incidents, approvals, evidence, assets, and identities, but those runtime changes require separate approved work.
