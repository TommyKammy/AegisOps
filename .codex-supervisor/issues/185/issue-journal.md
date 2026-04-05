# Issue #185: implementation: implement finding-to-alert ingest and alert upsert lifecycle

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/185
- Branch: codex/issue-185
- Workspace: .
- Journal: .codex-supervisor/issues/185/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: de402151bd7a3b208c963bb88a29d5297573e91b
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-05T01:11:27.103Z

## Latest Codex Summary
- Added the first service-level finding-to-alert ingest path with alert create/restatement handling keyed by correlation, plus reconciliation records that preserve `alert_id`, seen timestamps, ingest disposition, and linked finding/signal identifiers.
- Reproduced the missing lifecycle behavior with a new focused service test before implementation, then passed focused control-plane and schema verification.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The primary gap was not persistence itself but the absence of a reviewed ingest API that could convert upstream finding or analytic-signal input into alert records while preserving dedup/restatement linkage.
- What changed: Added `AegisOpsControlPlaneService.ingest_finding_alert`, store listing support for correlation lookup, expanded reconciliation metadata (`alert_id`, `first_seen_at`, `last_seen_at`, `ingest_disposition`), updated schema files, and added a focused reproducing test that now passes.
- Current blocker: none
- Next exact step: Commit this checkpoint, then decide whether to extend the ingest path beyond restatement handling into an explicit `updated` or `deduplicated` branch driven by materially-new-work inputs.
- Verification gap: No dedicated test yet covers a materially new update path that should reuse an alert without being classified as a restatement, and no HTTP/runtime entrypoint exists for external intake yet.
- Files touched: control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_postgres_store.py; postgres/control-plane/schema.sql; postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql; control-plane/aegisops_control_plane/__init__.py
- Rollback concern: Reconciliation schema and model now require the new ingest fields together; partial rollback would desynchronize runtime and schema expectations.
- Last focused command: bash scripts/test-verify-control-plane-schema-skeleton.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
