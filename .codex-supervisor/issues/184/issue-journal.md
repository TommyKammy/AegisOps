# Issue #184: implementation: add control-plane persistence layer and stable record identifiers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/184
- Branch: codex/issue-184
- Workspace: .
- Journal: .codex-supervisor/issues/184/issue-journal.md
- Current phase: draft_pr
- Attempt count: 9 (implementation=1, repair=1)
- Last head SHA: a8b8e75d186dccbbe2511d15037a3f9a88ddcf02
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T22:33:24.722Z

## Latest Codex Summary
No further code change is warranted inside this branch without widening scope into dependency/tooling work. I updated the issue journal handoff so the next step is explicit: keep PR #196 at the current in-process checkpoint or open follow-up work once PostgreSQL client tooling is approved.

I verified the handoff fields in the journal. The only tracked local change at this point is the journal update itself; the branch otherwise remains at the pushed draft-PR checkpoint.

Summary: Updated the journal handoff to mark PR #196 as the current in-process checkpoint pending a tooling/follow-up decision.
State hint: draft_pr
Blocked reason: none
Tests: `rg -n "Next exact step|Verification gap|Current blocker" .codex-supervisor/issues/184/issue-journal.md`
Next action: Hold PR #196 for review at the current in-process checkpoint, or open follow-up work for live PostgreSQL-backed persistence once PostgreSQL client tooling is approved.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was not an existing regression in schema assets; the runtime gap was that `PostgresControlPlaneStore` had no persistence API or typed record model, so the control-plane service could not authoritatively store or retrieve any approved record family.
- What changed: Added `control-plane/aegisops_control_plane/models.py` with typed record families for alert, case, evidence, observation, lead, recommendation, approval decision, action request, hunt, hunt run, AI trace, and reconciliation records; implemented in-process `save`/`get` behavior in `control-plane/aegisops_control_plane/adapters/postgres.py`; added service delegation methods in `control-plane/aegisops_control_plane/service.py`; added `control-plane/tests/test_postgres_store.py` to prove adapter-level round-trip persistence by AegisOps-owned identifiers, negative lookups by upstream linkage IDs, and explicit `persistence_mode="in_memory"` reporting; added `control-plane/tests/test_service_persistence.py` to verify the same invariant at the runtime service boundary; exposed `persistence_mode="in_memory"` in runtime snapshots so the current implementation fails closed about not yet being live PostgreSQL-backed; documented the current persistence status and PostgreSQL tooling dependency in `control-plane/README.md`; clarified the same limitation in `control-plane/config/local.env.sample`; and exported the reviewed record models from `aegisops_control_plane` package root for callers.
- Current blocker: none
- Next exact step: Hold PR #196 for review at the current in-process checkpoint, or open follow-up work for live PostgreSQL-backed persistence once explicit PostgreSQL client tooling is approved for the runtime environment.
- Verification gap: No live PostgreSQL integration exists yet; verification now covers adapter, service, and runtime-snapshot boundaries, but storage is still only in-process because neither a Python PostgreSQL client nor `psql` is available in this environment.
- Files touched: .codex-supervisor/issues/184/issue-journal.md; control-plane/README.md; control-plane/config/local.env.sample; control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_postgres_store.py; control-plane/tests/test_runtime_skeleton.py; control-plane/tests/test_service_persistence.py
- Rollback concern: Low. The new persistence API is additive and isolated to the control-plane runtime scaffold.
- Last focused command: python3 -m unittest discover -s control-plane/tests -v
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
