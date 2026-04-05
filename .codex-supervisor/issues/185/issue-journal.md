# Issue #185: implementation: implement finding-to-alert ingest and alert upsert lifecycle

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/185
- Branch: codex/issue-185
- Workspace: .
- Journal: .codex-supervisor/issues/185/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: fb6fbc08ba4d431cc1b436b2d30e38d8e780d767
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-05T01:17:54.763Z

## Latest Codex Summary
Implemented the first finding-to-alert ingest slice in the control-plane service. The new `ingest_finding_alert` flow in [service.py](control-plane/aegisops_control_plane/service.py#L90) creates an `AlertRecord` on first sighting, reuses that `alert_id` on restated signals with the same correlation key, and persists a `ReconciliationRecord` that now carries explicit `alert_id`, seen-window timestamps, ingest disposition, and linked upstream finding/signal IDs in [models.py](control-plane/aegisops_control_plane/models.py#L203) and [schema.sql](postgres/control-plane/schema.sql#L172).

The reproducer was added first in [test_service_persistence.py](control-plane/tests/test_service_persistence.py#L102), then implemented and committed as `fb6fbc0` (`Implement finding-to-alert ingest upsert`). I also updated the issue journal with the reproduced failure and current handoff state.

Tests run:
- `python3 -m unittest control-plane/tests/test_service_persistence.py`
- `python3 -m unittest control-plane/tests/test_postgres_store.py`
- `python3 -m unittest control-plane/tests/test_runtime_skeleton.py`
- `python3 -m unittest discover -s control-plane/tests`
- `bash scripts/test-verify-control-plane-schema-skeleton.sh`
- `rg -n "finding_id|analytic_signal_id|alert_id|dedup|restat|upsert" control-plane docs scripts`
- `rg -n "finding-to-alert|analytic signal|alert lifecycle" docs/control-plane-state-model.md docs/secops-domain-model.md`

Summary: Added a focused finding-to-alert ingest API with alert create/restatement upsert behavior and explicit reconciliation linkage, backed by a reproducing service test and schema/model updates.
State hint: implementing
Blocked reason: none
Tests: python3 -m unittest discover -s control-plane/tests; bash scripts/test-verify-control-plane-schema-skeleton.sh; requested rg verification commands
Next action: Extend the ingest lifecycle beyond restatement into an explicit materially-new update/dedup branch or wire this service API to a runtime intake entrypoint
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining gap after the first ingest slice was the missing materially-new update and duplicate classification branch, since the reviewed schema and docs already expected `updated` and `deduplicated` dispositions in addition to `created` and `restated`.
- What changed: Extended `AegisOpsControlPlaneService.ingest_finding_alert` with a `materially_new_work` flag so same-correlation signals now resolve to `updated` when they represent new analyst work, `deduplicated` when the upstream finding or signal was already linked, and `restated` only for new upstream identifiers that do not materially change work. The alert record now reuses the same `alert_id` while updating its upstream linkage on the `updated` branch, and the service test now covers all four dispositions.
- Current blocker: none
- Next exact step: Commit this checkpoint, then decide whether any follow-up runtime intake entrypoint is still needed for issue scope or whether this branch is ready for draft PR review as the reviewed ingest lifecycle slice.
- Verification gap: The service path is covered in-process, but there is still no external runtime intake entrypoint or transport-level contract test for invoking this ingest flow outside direct service calls.
- Files touched: control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_postgres_store.py; postgres/control-plane/schema.sql; postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql; control-plane/aegisops_control_plane/__init__.py; .codex-supervisor/issues/185/issue-journal.md
- Rollback concern: Reconciliation schema and model now require the new ingest fields together; partial rollback would desynchronize runtime and schema expectations.
- Last focused command: python3 -m unittest discover -s control-plane/tests
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- 2026-04-05: Added explicit `updated` and `deduplicated` ingest classifications with a `materially_new_work` service input. Verification passed: `python3 -m unittest control-plane/tests/test_service_persistence.py`, `python3 -m unittest control-plane/tests/test_postgres_store.py`, `python3 -m unittest control-plane/tests/test_runtime_skeleton.py`, `python3 -m unittest discover -s control-plane/tests`, `bash scripts/test-verify-control-plane-schema-skeleton.sh`, and the requested `rg` checks.
