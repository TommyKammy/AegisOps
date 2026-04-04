# Issue #184: implementation: add control-plane persistence layer and stable record identifiers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/184
- Branch: codex/issue-184
- Workspace: .
- Journal: .codex-supervisor/issues/184/issue-journal.md
- Current phase: draft_pr
- Attempt count: 7 (implementation=1, repair=6)
- Last head SHA: ab662e140bf6e953c9c7bcfc564ce398ee5e2932
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T22:25:24.829Z

## Latest Codex Summary
Added a matching persistence-mode caveat to [local.env.sample](control-plane/config/local.env.sample) so the sample `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN` placeholder no longer reads like live PostgreSQL storage is already wired. That keeps the branch consistent across code, tests, README, and local config.

Updated the issue journal handoff, reran the focused runtime tests plus the config/readme grep check, and pushed the change as `ab662e1` (`Clarify sample persistence mode`).

Exported the typed control-plane record models from the package root and added a focused import test so callers do not need to reach into internal module paths to use the reviewed persistence records.

Summary: Clarified the sample env file so it matches the current in-memory persistence reality and pushed it to draft PR #196.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane/tests/test_runtime_skeleton.py control-plane/tests/test_service_persistence.py -v`; `rg -n "persistence_mode=in_memory|PostgreSQL client tooling|AEGISOPS_CONTROL_PLANE_POSTGRES_DSN" control-plane/config/local.env.sample control-plane/README.md control-plane/aegisops_control_plane control-plane/tests`
Next action: Decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was not an existing regression in schema assets; the runtime gap was that `PostgresControlPlaneStore` had no persistence API or typed record model, so the control-plane service could not authoritatively store or retrieve any approved record family.
- What changed: Added `control-plane/aegisops_control_plane/models.py` with typed record families for alert, case, evidence, observation, lead, recommendation, approval decision, action request, hunt, hunt run, AI trace, and reconciliation records; implemented in-process `save`/`get` behavior in `control-plane/aegisops_control_plane/adapters/postgres.py`; added service delegation methods in `control-plane/aegisops_control_plane/service.py`; added `control-plane/tests/test_postgres_store.py` to prove adapter-level round-trip persistence by AegisOps-owned identifiers, negative lookups by upstream linkage IDs, and explicit `persistence_mode="in_memory"` reporting; added `control-plane/tests/test_service_persistence.py` to verify the same invariant at the runtime service boundary; exposed `persistence_mode="in_memory"` in runtime snapshots so the current implementation fails closed about not yet being live PostgreSQL-backed; documented the current persistence status and PostgreSQL tooling dependency in `control-plane/README.md`; clarified the same limitation in `control-plane/config/local.env.sample`; and exported the reviewed record models from `aegisops_control_plane` package root for callers.
- Current blocker: none
- Next exact step: Commit and push the package-root export cleanup to draft PR #196, then decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling.
- Verification gap: No live PostgreSQL integration exists yet; verification now covers adapter, service, and runtime-snapshot boundaries, but storage is still only in-process because neither a Python PostgreSQL client nor `psql` is available in this environment.
- Files touched: .codex-supervisor/issues/184/issue-journal.md; control-plane/README.md; control-plane/config/local.env.sample; control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_postgres_store.py; control-plane/tests/test_runtime_skeleton.py; control-plane/tests/test_service_persistence.py
- Rollback concern: Low. The new persistence API is additive and isolated to the control-plane runtime scaffold.
- Last focused command: python3 -m unittest discover -s control-plane/tests -v
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
