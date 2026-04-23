# AegisOps Runbook

This runbook defines the reviewed operator procedure for the current AegisOps startup and shutdown path.

It supplements `docs/requirements-baseline.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/control-plane-runtime-service-boundary.md` by turning the approved first-boot runtime contract into one repo-owned daily procedure.

It does not authorize environment-specific secrets in version control, optional-extension startup blockers, direct backend exposure, HA or multi-node operating patterns, or unsupported emergency shortcuts.

## 1. Purpose and Status

This document exists to define one reviewed startup and shutdown path that operators can rehearse without reconstructing the sequence from multiple phase notes.

The reviewed procedure is limited to the current first-boot runtime floor:

- the AegisOps control-plane service under `control-plane/`;
- PostgreSQL as the authoritative control-plane persistence dependency;
- the approved reverse proxy boundary as the only reviewed user-facing ingress path; and
- reviewed Wazuh-facing analytic-signal intake expectations.

Startup, restore, and operator-load assumptions referenced by this runbook must stay aligned with `docs/smb-footprint-and-deployment-profile-baseline.md`.

Until implementation-specific commands are approved, operators must treat first boot as limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

Operators must not treat optional OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path as first-boot prerequisites.

## 2. Startup

The reviewed startup path is business-hours oriented and must begin from a change-aware operator session with repository access, the approved runtime env file, and access to the reviewed secret source referenced by that env file.

### 2.1 Startup Preconditions

Before starting anything, the operator must confirm all of the following:

- the workspace is on the reviewed repository revision for the maintenance window or first-boot rehearsal;
- an untracked runtime env file has been prepared from `control-plane/deployment/first-boot/bootstrap.env.sample` without committing live secrets, DSNs, or tokens;
- the required Phase 17 runtime keys are present and intentionally set: `AEGISOPS_CONTROL_PLANE_HOST`, `AEGISOPS_CONTROL_PLANE_PORT`, `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`, `AEGISOPS_CONTROL_PLANE_BOOT_MODE`, and `AEGISOPS_CONTROL_PLANE_LOG_LEVEL`;
- `AEGISOPS_CONTROL_PLANE_BOOT_MODE` remains `first-boot`;
- the reviewed reverse-proxy-first ingress posture remains in force, with no plan to publish the control-plane backend port directly; and
- the operator has a place to capture startup evidence for the window, including command output, readiness results, and any refusal or retry reason.

Optional environment keys such as `AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL`, `AEGISOPS_CONTROL_PLANE_N8N_BASE_URL`, `AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL`, and `AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL` may remain unset without blocking startup.

If required bootstrap state is absent, malformed, contradictory, or would bypass the approved reverse-proxy boundary, startup must stop and remain failed closed instead of guessing a broader runtime context.

### 2.2 Reviewed Startup Sequence

The reviewed repo-owned startup sequence is:

1. Confirm the env file and secret references are ready without echoing secret values into the evidence record.
2. Start the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml up -d`.
3. Let the reviewed control-plane entrypoint perform runtime-config validation, PostgreSQL reachability proof, and migration bootstrap before the system is treated as ready.
4. Confirm the reverse proxy, not the backend container port, is the user-facing access path for health, readiness, and runtime inspection.
5. Capture the resulting container state and reviewed ingress evidence before admitting normal operator use.

The reviewed startup order is PostgreSQL dependency first, then the control-plane service with migration bootstrap, then the reverse proxy admission surface.

Operators must not reorder startup to make optional components authoritative, bypass the reverse proxy with direct backend publication, or treat partial container creation as proof of readiness.

### 2.3 Startup Evidence Capture

The minimum startup evidence set is:

- the reviewed repository revision or release identifier used for the startup window;
- confirmation that the runtime env file was sourced from the reviewed sample contract and kept untracked;
- `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml ps`;
- a bounded log capture from the startup window such as `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml logs --tail=200`;
- the reverse-proxy health result from `curl -fsS http://127.0.0.1:<proxy-port>/healthz`;
- the reverse-proxy readiness result from `curl -fsS http://127.0.0.1:<proxy-port>/readyz`; and
- the runtime inspection snapshot from `curl -fsS http://127.0.0.1:<proxy-port>/runtime`.

Evidence capture must record whether any startup step initially failed, what was corrected, and whether the final ready state was achieved without changing the approved boundary or adding new prerequisites.

Operators must redact or omit secret material from saved evidence.

### 2.4 Ready-to-Operate Checks

The platform may be treated as ready for the reviewed operational baseline only when all of the following are true:

- the control-plane service has not failed closed on missing runtime config, missing migration assets, PostgreSQL connection failure, partial migration application, or readiness-proof failure;
- `/healthz` succeeds through the reverse proxy;
- `/readyz` succeeds through the reverse proxy, proving required bootstrap state, PostgreSQL reachability, and the expected reviewed schema state;
- `/runtime` shows the reviewed first-boot surface rather than an expanded optional-extension claim;
- the operator can confirm the startup remained limited to the control-plane, PostgreSQL, reverse proxy, and reviewed Wazuh-facing first-boot boundary; and
- optional extensions, if shown at all, remain explicitly subordinate and non-blocking rather than being inferred as part of mainline readiness.

If readiness fails, operators must stop at evidence capture and correction review. They must not admit normal traffic, widen ingress, or substitute optional-extension health for first-boot readiness.

## 3. Shutdown

The reviewed shutdown path exists to return the platform to a clean, operator-confirmed safe state without leaving ambiguous runtime ownership or half-stopped ingress.

### 3.1 Controlled Shutdown Conditions

Controlled shutdown is permitted only when one of the following applies:

- a reviewed maintenance window is active;
- a restore, rollback, or platform hygiene change requires the runtime to stop cleanly; or
- the runtime has already failed a reviewed readiness or safety gate and operators need to preserve state while preventing further admission.

Shutdown must be paused for manual review if the operator cannot account for active review work, in-flight approval handling, unresolved reconciliation state, or another circumstance where immediate stop would make the audit trail or operator handoff ambiguous.

### 3.2 Reviewed Shutdown Sequence

The reviewed repo-owned shutdown sequence is:

1. Capture a final pre-shutdown readiness snapshot through the reverse proxy.
2. Record container state and bounded logs for the shutdown window.
3. Stop the reviewed first-boot runtime surface with `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml down`.
4. Confirm that the reverse proxy is no longer admitting the reviewed inspection and readiness routes.
5. Confirm the reviewed runtime surface is fully stopped before declaring the environment safe for follow-on maintenance, restore, or rollback work.

The shutdown order must preserve the operator evidence trail: inspect first, stop the repo-owned stack second, then confirm ingress withdrawal and runtime absence.

Operators must not use ad hoc container deletion, direct data-path manipulation, or undocumented shortcuts as the reviewed shutdown path.

### 3.3 Shutdown Evidence Capture

The minimum shutdown evidence set is:

- the shutdown reason and approved maintenance or recovery context;
- the final `curl -fsS http://127.0.0.1:<proxy-port>/readyz` result before stopping the stack, or the exact refusal if readiness was already unavailable;
- `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml ps` captured before shutdown;
- a bounded shutdown-window log capture such as `docker compose --env-file <runtime-env-file> -f control-plane/deployment/first-boot/docker-compose.yml logs --tail=200`; and
- post-stop confirmation that the reviewed stack is down and the proxy-facing routes are no longer serving the runtime.

If shutdown follows a fault, the evidence must preserve the failing signal instead of overwriting it with a clean retry narrative.

### 3.4 Safe-State Confirmation

Shutdown is complete only when operators can confirm all of the following:

- the reviewed compose stack reports no running first-boot services;
- the reverse proxy no longer exposes the reviewed `/healthz`, `/readyz`, or `/runtime` path for this stack;
- there is no claim that optional services remained authoritative or that the backend stayed intentionally exposed after shutdown; and
- the evidence record is sufficient for later restore, rollback, or health review work to understand the state that was stopped.

If any part of the stack remains running unexpectedly, shutdown is incomplete and must stay open until the drift is resolved or escalated.

## 4. Restore

This section defines the reviewed backup, restore, and rollback contract for the current AegisOps control-plane environment.

Before a reviewed platform change, operators must confirm the latest PostgreSQL-aware backup completed successfully, the reviewed configuration backup set is current, and the backup custody record identifies the named operator or break-glass owner for the window.

The approved backup set for restore and rollback readiness includes the PostgreSQL-aware backup, the reviewed repository revision or release identifier, the untracked runtime env file or equivalent reviewed configuration export, and any reviewed secret-source references needed to recreate runtime bindings without storing live secret values in Git.

Backup artifacts must remain separately custodied from the active runtime mounts, must stay attributable to the reviewed environment and time window, and must not be treated as valid if provenance, retention status, or operator ownership is ambiguous.

Restore must stop and remain failed closed if backup provenance, custody, completeness, or reviewed scope cannot be demonstrated from the evidence set.

The reviewed restore sequence is:

1. Capture the pre-restore state, including the last available readiness result, compose status, bounded logs, and the exact maintenance or failure reason that triggered recovery.
2. Confirm the reviewed backup set, the intended restore point, and the reviewed repository revision or release identifier before any durable state is replaced.
3. Execute the approved PostgreSQL-aware restore path and restore the reviewed configuration set needed to recreate runtime bindings without substituting guessed values, placeholder secrets, or ad hoc topology changes.
4. Restart the reviewed runtime only through the documented startup path in Section 2 and treat `/readyz` success as necessary but not sufficient for return to service.
5. Validate the restored environment against the authoritative record chain before normal operations resume and preserve the resulting evidence bundle with the restore ticket or maintenance record.

Restore validation before normal operations resume must confirm that:

- approval records remain linked to the reviewed case and action scope rather than disappearing behind backup age or partial restore drift;
- evidence records remain attributable, reviewable, and linked to the restored case, approval, execution, and reconciliation chain;
- execution records and receipts remain intact without orphaning partially restored downstream state;
- reconciliation records still describe the authoritative post-action outcome, including mismatch, pending, or terminal markers where they existed before recovery; and
- readiness, reverse-proxy admission, and runtime inspection all reflect the same committed restored state rather than a mixed snapshot assembled from different recovery points.

Operators must retain restore evidence showing the triggering reason, the selected restore point, the backup custody confirmation, the repository revision or release identifier used, the post-restore readiness checks, and the record-chain validation outcome before normal operations resume.

Rollback is the same-day operator path for returning from a reviewed change window to the prior known-good state when restore validation, readiness, or operator evidence shows the changed state is no longer trustworthy.

Rollback must begin when any of the following apply:

- the reviewed startup path succeeds but post-change validation shows missing or drifted approval, evidence, execution, or reconciliation records;
- readiness or runtime inspection exposes a degraded or contradictory state that operators cannot correct inside the approved maintenance window without widening scope;
- a reviewed configuration or schema change leaves the environment unable to resume the prior safe business-hours operating path; or
- operators cannot prove the changed state preserves the same authoritative record chain as the pre-change environment.

Operators must retain rollback evidence showing the trigger, the backup set or configuration revision used, the restoration point selected, the post-rollback readiness results, and the confirmation that the prior known-good approval, evidence, execution, and reconciliation chain was restored.

VM snapshots may support infrastructure recovery tasks, but they do not replace the reviewed PostgreSQL-aware backup, restore validation, or record-chain checks required by this contract.

This contract stays aligned with `docs/smb-footprint-and-deployment-profile-baseline.md` by requiring operator-led same-day rollback readiness, PostgreSQL-aware backup custody, and reconciliation-preserving restore validation instead of HA overbuild or snapshot-only recovery claims.

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

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure beyond the reviewed startup and shutdown path.

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
