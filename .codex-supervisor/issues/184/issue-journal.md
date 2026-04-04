# Issue #184: implementation: add control-plane persistence layer and stable record identifiers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/184
- Branch: codex/issue-184
- Workspace: .
- Journal: .codex-supervisor/issues/184/issue-journal.md
- Current phase: draft_pr
- Attempt count: 3 (implementation=1, repair=2)
- Last head SHA: fc561839f3cb685c423d31ca7c4b35516d9d0992
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T22:08:08.780Z

## Latest Codex Summary
Added a narrow runtime-facing verification slice in [test_service_persistence.py](control-plane/tests/test_service_persistence.py). It proves `AegisOpsControlPlaneService.persist_record()` and `get_record()` preserve AegisOps-owned identifiers for persisted records and do not resolve records by approval or n8n workflow-execution linkage fields.

Updated the issue journal handoff, committed the change as `fc56183` (`Add service persistence verification`), and pushed it to the existing draft PR. Remaining gap is unchanged: persistence is still in-process rather than backed by live PostgreSQL.

Made the current storage mode explicit by surfacing `persistence_mode="in_memory"` in runtime snapshots and covering it with focused tests, because the environment currently has neither a Python PostgreSQL client nor `psql`.

Summary: Added service-level persistence verification and pushed it to draft PR #196.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane/tests/test_service_persistence.py -v`; `python3 -m unittest discover -s control-plane/tests -v`
Next action: Decide whether issue #184 stops at this in-process persistence checkpoint or expands into live PostgreSQL-backed persistence work.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was not an existing regression in schema assets; the runtime gap was that `PostgresControlPlaneStore` had no persistence API or typed record model, so the control-plane service could not authoritatively store or retrieve any approved record family.
- What changed: Added `control-plane/aegisops_control_plane/models.py` with typed record families for alert, case, evidence, observation, lead, recommendation, approval decision, action request, hunt, hunt run, AI trace, and reconciliation records; implemented in-process `save`/`get` behavior in `control-plane/aegisops_control_plane/adapters/postgres.py`; added service delegation methods in `control-plane/aegisops_control_plane/service.py`; added `control-plane/tests/test_postgres_store.py` to prove adapter-level round-trip persistence by AegisOps-owned identifiers and negative lookups by upstream linkage IDs; added `control-plane/tests/test_service_persistence.py` to verify the same invariant at the runtime service boundary; exposed `persistence_mode="in_memory"` in runtime snapshots so the current implementation fails closed about not yet being live PostgreSQL-backed.
- Current blocker: none
- Next exact step: Commit and push the persistence-mode clarification to draft PR #196, then decide whether live PostgreSQL-backed persistence should be follow-up work gated on adding PostgreSQL client tooling.
- Verification gap: No live PostgreSQL integration exists yet; verification now covers adapter, service, and runtime-snapshot boundaries, but storage is still only in-process because neither a Python PostgreSQL client nor `psql` is available in this environment.
- Files touched: .codex-supervisor/issues/184/issue-journal.md; control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_postgres_store.py; control-plane/tests/test_service_persistence.py
- Rollback concern: Low. The new persistence API is additive and isolated to the control-plane runtime scaffold.
- Last focused command: python3 -m unittest discover -s control-plane/tests -v
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
