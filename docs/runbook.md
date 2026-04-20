# AegisOps Runbook Skeleton

This runbook is an initial skeleton for approved future operational procedures.

It supplements `docs/requirements-baseline.md` by reserving a structured home for startup, shutdown, restore, approval handling, and validation guidance as implementation artifacts mature.

It does not claim production completeness and does not authorize environment-specific commands.

## 1. Purpose and Status

This document exists to define the minimum approved structure for future operator procedures without implying that those procedures are complete today.

The current content is intentionally limited to placeholders, constraints, and documentation expectations that align with the AegisOps baseline.

Any future operational detail added here must remain consistent with the approved architecture, repository assets, and validation requirements.

Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.

## 2. Startup

Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist.

Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites.

Operators should size startup expectations, maintenance windows, and review burden against `docs/smb-footprint-and-deployment-profile-baseline.md` rather than against enterprise-cluster assumptions.

Future startup guidance should describe:

- approved prerequisites and dependencies,
- the order in which platform components may be started,
- the records or evidence operators must capture during startup, and
- the validation checkpoints required before the platform is treated as ready.

This section must not be expanded with environment-specific commands until those commands are backed by approved version-controlled artifacts.

## 3. Shutdown

Detailed shutdown steps are intentionally deferred until implementation artifacts and validation procedures exist.

Future shutdown guidance should describe:

- when a controlled shutdown is permitted,
- the sequence that preserves data integrity and auditability,
- what approvals or change records are required before shutdown, and
- what post-shutdown checks confirm the platform is in a safe state.

This section must not be expanded with unsupported emergency procedures or ad-hoc manual shortcuts.

## 4. Restore

Detailed restore steps are intentionally deferred until implementation artifacts and validation procedures exist.

Future restore guidance should describe:

- the approved restore inputs and dependencies,
- the order for restoring services and data-bearing components,
- how restore success is validated before normal operations resume, and
- what evidence must be retained for audit and review.

This section must not imply that hypervisor snapshots alone are a sufficient recovery procedure unless an approved ADR changes that baseline.

Restore planning should remain inside the backup and restore expectations published in `docs/smb-footprint-and-deployment-profile-baseline.md`.

## 5. Approval Handling

The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default.

Approval handling procedures must preserve human review, auditability, and the separation between detection and execution.

Future approval guidance should describe:

- who may approve which categories of actions,
- how approval decisions are recorded,
- how rejected or expired approvals are handled, and
- how operators verify that unapproved actions were not executed.

This section must remain consistent with the business-hours-oriented operating model and must not imply unrestricted autonomous response.

## 6. Validation

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure.

Future validation guidance should describe:

- the minimum checks required after startup, shutdown, or restore activity,
- the logs, alerts, or workflow evidence that must be reviewed,
- the conditions that require escalation instead of continued operation, and
- the repository artifacts that define the expected state.

The reviewed readiness surface must expose optional-extension operability explicitly instead of leaving operators to infer state from missing sidecars or quiet logs.

At minimum, validation should distinguish:

- `enabled` optional paths that are intentionally active but still non-authoritative;
- `disabled_by_default` optional paths that remain off without blocking the mainline;
- `unavailable` optional paths whose supporting runtime is absent or intentionally not configured; and
- `degraded` optional paths whose reviewed receipts, health, or bounded outputs are lagging and therefore require operator-visible follow-up.

Validation must confirm that optional assistant, endpoint evidence, optional network evidence, and ML shadow paths stay subordinate to the reviewed control-plane chain even when their operability state is `unavailable` or `degraded`.

The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.

This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours.

### 6.1 Selected Slice and Preconditions

The selected replay-to-detection-to-notify slice covers these reviewed use cases only:

1. Privileged group membership change
2. Audit log cleared
3. New local user created

The operator should treat the slice as ready for analyst validation only when all of the following repository artifacts remain present and internally consistent:

- `docs/phase-6-initial-telemetry-slice.md`
- `docs/source-families/windows-security-and-endpoint/onboarding-package.md`
- `docs/phase-6-opensearch-detector-artifact-validation.md`
- `opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml`
- `opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml`
- `opensearch/detectors/windows-security-and-endpoint/new-local-user-created-staging.yaml`
- `n8n/workflows/aegisops_enrich/aegisops_enrich_windows_selected_detector_outputs.json`
- `n8n/workflows/aegisops_notify/aegisops_notify_windows_selected_detector_outputs.json`
- `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`

This slice is not a production activation checklist. It does not authorize live source onboarding, detector enablement against production indexes, response execution, or after-hours operation promises.

### 6.2 Analyst Validation Path

The analyst validation path for this slice is review-first and replay-oriented:

1. Confirm the replay corpus still represents only the three selected Windows use cases and remains synthetic or redacted review material.
2. Confirm each detector artifact remains `staging` scoped, points to `aegisops-logs-windows-staging-*`, and preserves the expected field dependencies and replay evidence references.
3. Confirm the enrich workflow remains read-only and the notify workflow remains notify-only, with no write-capable connector, response step, or approval-bypass behavior inferred from the asset content.
4. Exercise the slice by replaying the reviewed success-path records into the approved staging validation path and verifying that the resulting detector outputs are suitable for analyst review rather than automated action.
5. Review the resulting routed work item during business hours and confirm it can be handled as a queue-driven analyst task with evidence capture, hypothesis development, and escalation or closure decisions remaining human-owned.

Validation is incomplete if the slice depends on missing actor attribution, forwarded-event timing ambiguity, hidden field remapping, threshold logic, or any workflow behavior beyond the approved read-only and notify-only boundaries.

### 6.3 Required Evidence Review

Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.

The minimum evidence review for each exercise is:

- replay evidence showing which of the three selected Windows scenarios was used;
- detector metadata showing the expected validation target index, Sigma traceability, field dependencies, and false-positive notes;
- workflow metadata showing the enrich asset remains read-oriented and the notify asset remains analyst-routing only; and
- analyst-facing review notes showing whether the routed output was understandable, attributable to the replayed record, and compatible with the business-hours queue model.

Any validation record should note whether the slice produced an explainable analyst work item, whether the evidence was sufficient for same-day review, and whether the output should stay staged, be revised, or be withdrawn.

### 6.4 Disable and Rollback Path

If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.

Rollback for this slice means returning to the prior safe state where the reviewed artifacts remain version-controlled reference material only:

- do not promote the detector artifacts beyond staging-only scope;
- do not treat replay success as authority for production index coverage;
- do not leave the selected enrich or notify assets available for uncontrolled live routing if their analyst-facing output is misleading or incomplete; and
- document the failure reason, the affected use case, and the artifact set withdrawn from validation so the next review can confirm the rollback state deliberately.

Escalate instead of continuing validation when the failure suggests missing provenance, ambiguous timestamps, missing identity fields required by the detector, or any behavior that would make the routed work item unreliable for analyst review.

The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation.
