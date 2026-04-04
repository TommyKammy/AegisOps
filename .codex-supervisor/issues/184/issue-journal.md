# Issue #184: implementation: add control-plane persistence layer and stable record identifiers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/184
- Branch: codex/issue-184
- Workspace: .
- Journal: .codex-supervisor/issues/184/issue-journal.md
- Current phase: draft_pr
- Attempt count: 6 (implementation=1, repair=5)
- Last head SHA: 6bfac6f6f4f96b5eaff0b9d6f29e786177608bd5
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T22:21:00.880Z

## Latest Codex Summary
Added a direct adapter-level check in [test_postgres_store.py](control-plane/tests/test_postgres_store.py) so `PostgresControlPlaneStore` now explicitly proves `persistence_mode == "in_memory"` in addition to the existing round-trip ID tests. That makes the current storage contract consistent across adapter, service, and runtime-snapshot coverage.

Updated the issue journal handoff, reran the focused test suite, and pushed the follow-up as `6bfac6f` (`Verify adapter persistence mode`).

Added a matching note to `control-plane/config/local.env.sample` so the sample PostgreSQL DSN placeholder no longer implies live PostgreSQL-backed storage without the required client tooling.

Summary: Added adapter-level persistence-mode verification and pushed it to draft PR #196.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane/tests/test_postgres_store.py -v`; `python3 -m unittest discover -s control-plane/tests -v`
Next action: Decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was not an existing regression in schema assets; the runtime gap was that `PostgresControlPlaneStore` had no persistence API or typed record model, so the control-plane service could not authoritatively store or retrieve any approved record family.
- What changed: Added `control-plane/aegisops_control_plane/models.py` with typed record families for alert, case, evidence, observation, lead, recommendation, approval decision, action request, hunt, hunt run, AI trace, and reconciliation records; implemented in-process `save`/`get` behavior in `control-plane/aegisops_control_plane/adapters/postgres.py`; added service delegation methods in `control-plane/aegisops_control_plane/service.py`; added `control-plane/tests/test_postgres_store.py` to prove adapter-level round-trip persistence by AegisOps-owned identifiers, negative lookups by upstream linkage IDs, and explicit `persistence_mode="in_memory"` reporting; added `control-plane/tests/test_service_persistence.py` to verify the same invariant at the runtime service boundary; exposed `persistence_mode="in_memory"` in runtime snapshots so the current implementation fails closed about not yet being live PostgreSQL-backed; documented the current persistence status and PostgreSQL tooling dependency in `control-plane/README.md`; and clarified the same limitation in `control-plane/config/local.env.sample`.
- Current blocker: none
- Next exact step: Commit and push the config-sample clarification to draft PR #196, then decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling.
- Verification gap: No live PostgreSQL integration exists yet; verification now covers adapter, service, and runtime-snapshot boundaries, but storage is still only in-process because neither a Python PostgreSQL client nor `psql` is available in this environment.
- Files touched: .codex-supervisor/issues/184/issue-journal.md; control-plane/README.md; control-plane/config/local.env.sample; control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_postgres_store.py; control-plane/tests/test_service_persistence.py
- Rollback concern: Low. The new persistence API is additive and isolated to the control-plane runtime scaffold.
- Last focused command: rg -n "persistence_mode=in_memory|PostgreSQL client tooling|AEGISOPS_CONTROL_PLANE_POSTGRES_DSN" control-plane/config/local.env.sample control-plane/README.md control-plane/aegisops_control_plane control-plane/tests
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
