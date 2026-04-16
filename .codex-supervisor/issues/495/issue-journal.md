# Issue #495: implementation: add stale / degraded / silent-failure detection for ingest, delegation, provider, and persistence paths

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/495
- Branch: codex/issue-495
- Workspace: .
- Journal: .codex-supervisor/issues/495/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 8 (implementation=1, repair=7)
- Last head SHA: 532d7aa461598bc7010ed927510faca7121b524f
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-16T20:15:20.556Z

## Latest Codex Summary
Promoted overdue reviewed-path health in [service.py](control-plane/aegisops_control_plane/service.py:2149) so expired approval and execution windows no longer remain indefinitely `delayed`. Approved reviews with no delegation now age into the existing missing-after-approval degraded reasons, and overdue execution-linked gaps surface explicit timeout reasons for ingest, delegation receipt, provider receipt or authoritative outcome, and reconciliation.

Added focused regressions in [test_service_persistence_restore_readiness.py](control-plane/tests/test_service_persistence_restore_readiness.py:1784) and [test_cli_inspection.py](control-plane/tests/test_cli_inspection.py:4010). The code change is committed as `532d7aa` with message `Promote overdue reviewed path health`. The issue journal working notes were updated; the `.codex-supervisor` files remain untracked local metadata.

Summary: Promoted overdue reviewed path health to explicit degraded timeout and missing-after-approval states, added readiness/CLI regressions, and committed the fix as `532d7aa`.
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m py_compile control-plane/aegisops_control_plane/service.py control-plane/tests/test_service_persistence_restore_readiness.py control-plane/tests/test_cli_inspection.py`; `python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness`; `python3 -m unittest control-plane.tests.test_cli_inspection`
Next action: Run a fresh local review on commit `532d7aa` / PR #502 to confirm the overdue-path-health repair clears the remaining must-fix residue.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining local-review blocker was the readiness candidate builder dropping reviewed actions whose unresolved reconciliation only linked back through `delegation_ids`, because `_build_readiness_review_path_health()` seeded candidates from action request, approval, and execution linkage but never from delegation lineage.
- What changed: Added `_readiness_candidate_action_request_ids_for_delegations()` in `service.py` so unresolved reconciliation `delegation_ids` seed reviewed action requests before readiness path classification. The Postgres readiness helper now accepts optional `delegation_ids` and can fetch matching executions without falling back to full-table scans, the fake-store passthroughs were widened to the same signature, and `postgres_test_support.py` now recognizes the delegation lookup query. Added a focused regression in `test_service_persistence_restore_readiness.py` proving a completed reviewed action with a delegation-only stale reconciliation still surfaces degraded persistence visibility without `list()` scans.
- Current blocker: none
- Next exact step: Run a fresh local review pass on the new repair commit / PR #502 head to confirm the delegation-lineage readiness gap is cleared.
- Verification gap: The issue text references a Phase 23 degraded-mode validation module that does not exist in the current tree; verification is currently anchored to the live CLI/readiness suites.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/aegisops_control_plane/adapters/postgres.py; control-plane/tests/support/fake_store.py; control-plane/tests/test_service_persistence_restore_readiness.py; control-plane/postgres_test_support.py; .codex-supervisor/issues/495/issue-journal.md
- Rollback concern: Low. The runtime change is limited to reviewed readiness candidate seeding and a narrow Postgres helper expansion; reverting it would reintroduce the blind spot where delegation-linked stale/mismatched reconciliations disappear once the action request and execution leave the active sets.
- Last focused command: python3 -m unittest control-plane.tests.test_cli_inspection
- Exact failure encountered: The first readiness regression attempt expected a `pending` reconciliation to promote readiness to `degraded`, but the service correctly leaves `pending` as delayed/ready; the test was tightened to the actual lost degraded case by using a `stale` reconciliation. Adding the new Postgres delegation lookup also required teaching `postgres_test_support.py` to match `where delegation_id in (...)` queries.
- Commands run: `python3 -m py_compile control-plane/aegisops_control_plane/service.py control-plane/aegisops_control_plane/adapters/postgres.py control-plane/tests/support/fake_store.py control-plane/tests/test_service_persistence_restore_readiness.py control-plane/postgres_test_support.py`; `python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness`; `python3 -m unittest control-plane.tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
