# AegisOps Retention, Evidence Lifecycle, and Replay Readiness Baseline

## 1. Purpose

This document defines the baseline retention classes, evidence lifecycle assumptions, and replay readiness expectations for AegisOps-owned records.

It supplements `docs/requirements-baseline.md`, `docs/storage-layout-and-mount-policy.md`, `docs/runbook.md`, `docs/control-plane-state-model.md`, and `docs/response-action-safety-model.md` by making policy-level retention and restore expectations explicit before any runtime storage lifecycle is implemented.

This document defines baseline policy only. It does not introduce live ILM policies, index rollovers, shard sizing, snapshot schedules, database retention jobs, or production storage tier configuration in this phase.

## 2. Retention Classes

Retention classes must remain reviewable by record family rather than inherited implicitly from whichever component currently stores the data.

The baseline classes below define relative expectations for hot, warm, cold, and archival handling. Concrete day counts, index ages, bucket policies, and storage sizes remain future implementation parameters.

| Record family | Baseline retention class | Policy-level expectation |
| ---- | ---- | ---- |
| `Raw Event` | Shorter-lived high-volume telemetry | Keep hot retention limited to the period needed for immediate triage, parser troubleshooting, and near-term detection review. Warm or cold retention may be used for short historical reach, but raw events should age out before normalized investigative records unless an approved source-specific need requires longer preservation. |
| `Normalized Event` | Medium-lived operational analysis record | Retain longer than raw events so analysts can investigate, correlate, and re-run approved detection or mapping checks after raw payload windows expire. Normalized events are the default replay substrate for most platform-level validation and investigation work. |
| `Finding` | Medium-lived analytics outcome | Retain long enough to support alert review, tuning analysis, false-positive tracking, and post-incident reconstruction of why the analytics layer produced a result. Findings may roll from hot to warm storage once active triage pressure drops. |
| `Alert` | Longer-lived operator work and audit record | Retain longer than findings because alert lifecycle, analyst disposition, escalation, and linkage to cases or response actions remain part of the durable audit trail. Alert records should remain recoverable even after the originating analytics-plane artifacts have moved to colder storage. |
| `Evidence` | Case and audit preservation record | Retain longer than alerts when the record substantiates analyst conclusions, approvals, execution outcomes, or incident reporting. Evidence must support hot access for active work, warm access for routine review, and cold or archive preservation for closed investigations that still require auditability. |
| `Approval Decision` | Durable control and audit record | Retain at least as long as the evidence and execution records needed to prove who approved or rejected a request, under what scope, and with what expiry or conditions. Approval records must not age out before the linked execution and verification trail. |
| `Action Execution` | Durable execution and reconciliation record | Retain long enough to reconstruct what downstream action actually ran, whether it matched approved intent, what verification evidence was collected, and whether retry or manual recovery occurred. Execution records must remain reviewable alongside the approval and evidence they reference. |

Retention changes for any class above must be explicit, documented, and approved rather than emerging indirectly from default component behavior.

## 3. Replay Dataset and Restore Readiness Expectations

Replay-capable datasets must be retained long enough to support parser validation, rule validation, and targeted historical reprocessing for approved investigations and recovery exercises.

The baseline replay assumption is that representative normalized datasets are the primary future replay input, while selected raw-event samples may be preserved where parser validation, provenance review, or source-specific troubleshooting requires them.

Replay readiness must preserve enough provenance, timestamp fidelity, source-family context, and schema version context that future operators can explain what a replay dataset represents and what it cannot prove.

Restore readiness must assume application-aware restore procedures for OpenSearch, PostgreSQL, and future platform-owned control records rather than treating hypervisor snapshots as the primary recovery model.

Hypervisor snapshots may assist short-lived infrastructure rollback or maintenance windows, but they are supplemental tooling only and must not be treated as the authoritative replay or disaster-recovery baseline for AegisOps data.

Policy-level storage expectations for future sizing and readiness work are:

- hot retention exists for records required for current triage, active workflow execution, and recent validation;
- warm retention exists for records that remain routinely searchable without claiming top-tier performance;
- cold or archive retention exists for records kept mainly for audit, investigation follow-up, selective replay, or regulated preservation;
- and rollover, compaction, or dataset handoff decisions must preserve record family boundaries and restore traceability rather than optimizing only for storage efficiency.

Future validation work must prove that retained replay datasets, retained approval records, and retained execution evidence can be restored or reviewed together closely enough to reconstruct a decision chain without depending on one component's incidental log detail.

## 4. Evidence Lifecycle and Legal-Hold Baseline

Evidence retention must preserve chain-of-custody context, source provenance, review references, and legal-hold status long enough to support audit, investigation, and post-incident review.

Evidence lifecycle handling must distinguish between:

- active evidence still being collected or reviewed;
- closed but routinely reviewable evidence for completed investigations or approvals;
- colder evidence kept mainly for audit, compliance, dispute resolution, or later replay support; and
- explicitly held evidence whose expiration is suspended.

Evidence references must remain stable enough that linked alerts, approvals, and action execution records do not become unverifiable when underlying artifacts move between storage classes.

Legal hold must suspend ordinary expiration for specifically scoped evidence and related approval or execution records until the hold is explicitly released through approved process.

When legal hold applies, the baseline expectation is to preserve the minimum linked record set needed to keep evidence interpretable: custody context, ownership annotations, approval context where relevant, execution outcomes where relevant, and the release decision when the hold ends.

This baseline does not approve a runtime legal-hold service, case-management product, or storage lock mechanism. It requires only that future implementations preserve the concept and do not design ordinary retention in a way that makes legal hold impossible.

## 5. Lifecycle Policy Constraints

This baseline defines policy-level hot, warm, cold, or rollover expectations only. It does not introduce live ILM policies, shard counts, index templates, storage tier automation, or production retention settings in this phase.

No record family may rely on container filesystem layers, dashboard state, ad hoc exports, or hypervisor snapshots as its sole long-term retention mechanism.

No future retention implementation may dissolve approval, evidence, or execution records into a single component-local history stream if that would make replay, audit, or restore validation ambiguous.

Parameterization of concrete durations, tier thresholds, rollover triggers, backup schedules, and restore objectives must remain in future approved parameter documents, runbooks, or ADRs once the implementation approach is chosen.

## 6. Baseline Alignment Notes

This baseline keeps retention and replay expectations explicit without pretending that current repository scaffolding already provides a production retention implementation.

It remains aligned with the storage policy rule that application-aware backup and restore take precedence over hypervisor snapshots, the runbook rule that restore evidence must be reviewable, and the control-plane state model rule that approvals and execution are first-class records rather than incidental workflow logs.

## 7. Audit Export Baseline

Audit exports must derive from AegisOps authoritative control-plane records rather than tickets, assistant output, ML output, endpoint evidence, network evidence, browser state, optional extension state, downstream receipts, or component-local logs.

Audit export reads must be snapshot-consistent. If the exporter cannot read the authoritative record chain from one committed snapshot, it must reject or escalate instead of stitching together mixed-state records.

Exported evidence payloads must be labeled as subordinate evidence. The export may include bounded, redacted subordinate evidence context only to explain the authoritative AegisOps record; it must not promote subordinate evidence into approval, execution, reconciliation, case-lifecycle, or commercial-readiness authority.

Export artifacts must not contain live secrets, placeholder credentials treated as valid credentials, raw authorization headers, private keys, workstation-local absolute paths, or unredacted source payloads that are not needed for the bounded audit baseline.

The retention baseline is bounded. It does not promise unlimited raw log retention, enterprise SIEM archive behavior, customer portal packaging, compliance certification, or production storage lifecycle automation.

The Phase 49.2 export schema records the bounded retention posture explicitly with `unlimited_log_retention` set to `false` and `compliance_certification_claim` set to `false`.
