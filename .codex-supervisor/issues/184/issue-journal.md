# Issue #184: implementation: add control-plane persistence layer and stable record identifiers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/184
- Branch: codex/issue-184
- Workspace: .
- Journal: .codex-supervisor/issues/184/issue-journal.md
- Current phase: draft_pr
- Attempt count: 5 (implementation=1, repair=4)
- Last head SHA: dea33262dc42611f5be3ee96cb604f2131d4add2
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T22:17:04.647Z

## Latest Codex Summary
Added a reviewer-facing persistence status section to [README.md](control-plane/README.md) that states the current control-plane runtime has typed record models plus `save()`/`get()` behavior, but still reports `persistence_mode="in_memory"` and is not live PostgreSQL-backed. This keeps the draft PR self-explanatory without requiring readers to infer the gap from tests alone.

Updated the issue journal handoff, reran the focused runtime tests, and pushed the doc follow-up as `dea3326` (`Document persistence status`).

Added an adapter-level test for `PostgresControlPlaneStore.persistence_mode` so the in-memory fallback is now asserted at the adapter, service, and runtime-snapshot boundaries.

Summary: Documented the current in-memory persistence status and pushed it to draft PR #196.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane/tests/test_runtime_skeleton.py control-plane/tests/test_service_persistence.py -v`; `rg -n "persistence_mode|Current persistence status|in_memory|Live PostgreSQL persistence remains follow-up work" control-plane/README.md control-plane/aegisops_control_plane control-plane/tests`
Next action: Decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was not an existing regression in schema assets; the runtime gap was that `PostgresControlPlaneStore` had no persistence API or typed record model, so the control-plane service could not authoritatively store or retrieve any approved record family.
- What changed: Added `control-plane/aegisops_control_plane/models.py` with typed record families for alert, case, evidence, observation, lead, recommendation, approval decision, action request, hunt, hunt run, AI trace, and reconciliation records; implemented in-process `save`/`get` behavior in `control-plane/aegisops_control_plane/adapters/postgres.py`; added service delegation methods in `control-plane/aegisops_control_plane/service.py`; added `control-plane/tests/test_postgres_store.py` to prove adapter-level round-trip persistence by AegisOps-owned identifiers, negative lookups by upstream linkage IDs, and explicit `persistence_mode="in_memory"` reporting; added `control-plane/tests/test_service_persistence.py` to verify the same invariant at the runtime service boundary; exposed `persistence_mode="in_memory"` in runtime snapshots so the current implementation fails closed about not yet being live PostgreSQL-backed; documented the current persistence status and PostgreSQL tooling dependency in `control-plane/README.md`.
- Current blocker: none
- Next exact step: Commit and push the adapter-level persistence-mode test to draft PR #196, then decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling.
- Verification gap: No live PostgreSQL integration exists yet; verification now covers adapter, service, and runtime-snapshot boundaries, but storage is still only in-process because neither a Python PostgreSQL client nor `psql` is available in this environment.
- Files touched: .codex-supervisor/issues/184/issue-journal.md; control-plane/README.md; control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_postgres_store.py; control-plane/tests/test_service_persistence.py
- Rollback concern: Low. The new persistence API is additive and isolated to the control-plane runtime scaffold.
- Last focused command: python3 -m unittest discover -s control-plane/tests -v
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
