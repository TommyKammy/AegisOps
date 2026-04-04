# Issue #184: implementation: add control-plane persistence layer and stable record identifiers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/184
- Branch: codex/issue-184
- Workspace: .
- Journal: .codex-supervisor/issues/184/issue-journal.md
- Current phase: draft_pr
- Attempt count: 4 (implementation=1, repair=3)
- Last head SHA: a61536839bf2b97ed303384937c7ed65cffab080
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T22:13:04.213Z

## Latest Codex Summary
Made the current storage status explicit instead of implying live PostgreSQL support. [postgres.py](control-plane/aegisops_control_plane/adapters/postgres.py) now exposes `persistence_mode="in_memory"`, [service.py](control-plane/aegisops_control_plane/service.py) includes that in the runtime snapshot, and the runtime/service tests were updated in [test_runtime_skeleton.py](control-plane/tests/test_runtime_skeleton.py) and [test_service_persistence.py](control-plane/tests/test_service_persistence.py).

This keeps the draft PR fail-closed about the remaining gap: the environment has neither a Python PostgreSQL client nor `psql`, so storage is still in-process. I updated the issue journal, committed the change as `a615368`, and pushed it to `codex/issue-184`.

Added a short `Current persistence status` section to `control-plane/README.md` so reviewers can see the branch-level storage boundary and remaining PostgreSQL tooling gap without reading the test files first.

Summary: Clarified and tested that the current control-plane persistence layer is explicitly in-memory, not live PostgreSQL-backed.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane/tests/test_runtime_skeleton.py control-plane/tests/test_service_persistence.py -v`; `python3 -m unittest discover -s control-plane/tests -v`
Next action: Decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling to the runtime environment.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was not an existing regression in schema assets; the runtime gap was that `PostgresControlPlaneStore` had no persistence API or typed record model, so the control-plane service could not authoritatively store or retrieve any approved record family.
- What changed: Added `control-plane/aegisops_control_plane/models.py` with typed record families for alert, case, evidence, observation, lead, recommendation, approval decision, action request, hunt, hunt run, AI trace, and reconciliation records; implemented in-process `save`/`get` behavior in `control-plane/aegisops_control_plane/adapters/postgres.py`; added service delegation methods in `control-plane/aegisops_control_plane/service.py`; added `control-plane/tests/test_postgres_store.py` to prove adapter-level round-trip persistence by AegisOps-owned identifiers and negative lookups by upstream linkage IDs; added `control-plane/tests/test_service_persistence.py` to verify the same invariant at the runtime service boundary; exposed `persistence_mode="in_memory"` in runtime snapshots so the current implementation fails closed about not yet being live PostgreSQL-backed; documented the current persistence status and PostgreSQL tooling dependency in `control-plane/README.md`.
- Current blocker: none
- Next exact step: Commit and push the README clarification to draft PR #196, then decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling.
- Verification gap: No live PostgreSQL integration exists yet; verification now covers adapter, service, and runtime-snapshot boundaries, but storage is still only in-process because neither a Python PostgreSQL client nor `psql` is available in this environment.
- Files touched: .codex-supervisor/issues/184/issue-journal.md; control-plane/README.md; control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_postgres_store.py; control-plane/tests/test_service_persistence.py
- Rollback concern: Low. The new persistence API is additive and isolated to the control-plane runtime scaffold.
- Last focused command: rg -n "persistence_mode|Current persistence status|in_memory|Live PostgreSQL persistence remains follow-up work" control-plane/README.md control-plane/aegisops_control_plane control-plane/tests
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
