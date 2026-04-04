# Issue #184: implementation: add control-plane persistence layer and stable record identifiers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/184
- Branch: codex/issue-184
- Workspace: .
- Journal: .codex-supervisor/issues/184/issue-journal.md
- Current phase: draft_pr
- Attempt count: 2 (implementation=1, repair=1)
- Last head SHA: 7b4db41cda23db72f88c8fd4c669133488302795
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T22:03:45.859Z

## Latest Codex Summary
Implemented the first control-plane persistence slice in [models.py](control-plane/aegisops_control_plane/models.py), [postgres.py](control-plane/aegisops_control_plane/adapters/postgres.py), and [service.py](control-plane/aegisops_control_plane/service.py). The runtime now has typed record families for the reviewed Phase 9 control-plane records plus `save()`/`get()` persistence behavior keyed on AegisOps-owned IDs, with explicit linkage fields preserved instead of treating OpenSearch or n8n identifiers as lifecycle keys.

Added the focused reproducing/verification test in [test_postgres_store.py](control-plane/tests/test_postgres_store.py), committed the work on `codex/issue-184` (`7b4db41`), pushed the branch, and opened draft PR [#196](https://github.com/TommyKammy/AegisOps/pull/196). Remaining gap: this is still an in-process persistence layer, not live PostgreSQL-backed integration yet. The only leftover local changes are untracked supervisor files under `.codex-supervisor/`.

Added `control-plane/tests/test_service_persistence.py` to verify the runtime service itself round-trips persisted records by AegisOps-owned identifiers and does not resolve records by approval or workflow-execution linkage fields.

Summary: Added typed control-plane persistence records, focused store/retrieve tests, pushed branch, and opened draft PR #196.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane/tests/test_postgres_store.py -v`; `python3 -m unittest discover -s control-plane/tests -v`; `rg -n "alert_id|case_id|evidence_id|observation_id|lead_id|recommendation_id|hunt_id|hunt_run_id|ai_trace_id|approval_decision_id|action_request_id" control-plane postgres`; `rg -n "finding_id|analytic_signal_id|workflow_execution_id|idempotency" control-plane postgres`
Next action: Extend this checkpoint toward live PostgreSQL-backed persistence or service-level persistence verification on PR #196.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was not an existing regression in schema assets; the runtime gap was that `PostgresControlPlaneStore` had no persistence API or typed record model, so the control-plane service could not authoritatively store or retrieve any approved record family.
- What changed: Added `control-plane/aegisops_control_plane/models.py` with typed record families for alert, case, evidence, observation, lead, recommendation, approval decision, action request, hunt, hunt run, AI trace, and reconciliation records; implemented in-process `save`/`get` behavior in `control-plane/aegisops_control_plane/adapters/postgres.py`; added service delegation methods in `control-plane/aegisops_control_plane/service.py`; added `control-plane/tests/test_postgres_store.py` to prove adapter-level round-trip persistence by AegisOps-owned identifiers and negative lookups by upstream linkage IDs; added `control-plane/tests/test_service_persistence.py` to verify the same invariant at the runtime service boundary.
- Current blocker: none
- Next exact step: Commit and push the service-level persistence verification update to draft PR #196, then decide whether issue #184 should stop at this in-process persistence checkpoint or grow into live PostgreSQL-backed storage work in a follow-up issue.
- Verification gap: No live PostgreSQL integration exists yet; verification now covers adapter and service boundaries, but still only in-process.
- Files touched: .codex-supervisor/issues/184/issue-journal.md; control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_postgres_store.py; control-plane/tests/test_service_persistence.py
- Rollback concern: Low. The new persistence API is additive and isolated to the control-plane runtime scaffold.
- Last focused command: python3 -m unittest discover -s control-plane/tests -v
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
