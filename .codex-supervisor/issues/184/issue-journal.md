# Issue #184: implementation: add control-plane persistence layer and stable record identifiers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/184
- Branch: codex/issue-184
- Workspace: .
- Journal: .codex-supervisor/issues/184/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: eaf135d9b2ae0d0e2216b671ab46e7afef85c412
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T21:55:17.846Z

## Latest Codex Summary
- Added the first typed control-plane persistence slice in `control-plane/` with explicit AegisOps-owned identifiers for the reviewed record families, plus a focused adapter test that proves records round-trip by control-plane IDs rather than OpenSearch or n8n linkage fields.
- Pushed `codex/issue-184` at `cc73aa8` and opened draft PR #196 (`[codex] Add control-plane persistence records`).

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was not an existing regression in schema assets; the runtime gap was that `PostgresControlPlaneStore` had no persistence API or typed record model, so the control-plane service could not authoritatively store or retrieve any approved record family.
- What changed: Added `control-plane/aegisops_control_plane/models.py` with typed record families for alert, case, evidence, observation, lead, recommendation, approval decision, action request, hunt, hunt run, AI trace, and reconciliation records; implemented in-process `save`/`get` behavior in `control-plane/aegisops_control_plane/adapters/postgres.py`; added service delegation methods in `control-plane/aegisops_control_plane/service.py`; added `control-plane/tests/test_postgres_store.py` to prove round-trip persistence by AegisOps-owned identifiers and negative lookups by upstream linkage IDs.
- Current blocker: none
- Next exact step: Decide whether to keep extending this issue with service-level or live-Postgres persistence verification, or hand the draft PR off for review as the first coherent checkpoint for issue #184.
- Verification gap: No live PostgreSQL integration exists yet; current verification is unit-level and in-process only.
- Files touched: .codex-supervisor/issues/184/issue-journal.md; control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/aegisops_control_plane/models.py; control-plane/aegisops_control_plane/service.py; control-plane/tests/test_postgres_store.py
- Rollback concern: Low. The new persistence API is additive and isolated to the control-plane runtime scaffold.
- Last focused command: gh pr create --draft --base main --head codex/issue-184 --title "[codex] Add control-plane persistence records" --body-file "$tmpfile"
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
