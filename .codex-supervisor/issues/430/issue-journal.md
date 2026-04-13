# Issue #430: implementation: keep requester identity inside the Phase 20 action-request deduplication boundary

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/430
- Branch: codex/issue-430
- Workspace: .
- Journal: .codex-supervisor/issues/430/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 859bc268e8f7a18fcce2d85ae5cbdb7fd65daa8f
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-13T00:41:02.529Z

## Latest Codex Summary
- Reproduced Phase 20 reviewed action-request deduplication reusing the same record across different `requester_identity` values.
- Added a focused persistence test for the `analyst-001` then `analyst-002` scenario and fixed the dedup boundary by including `requester_identity` in the reviewed action-request idempotency material.
- Focused Phase 20 request creation, approval/delegation, reconciliation, and validation tests passed after the change.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Reviewed Phase 20 action-request reuse was keyed too broadly because `requester_identity` was excluded from the idempotency material used for deduplication.
- What changed: Added a focused service persistence test covering `analyst-001` then `analyst-002`; updated `create_reviewed_action_request_from_advisory` so the idempotency key now includes `requester_identity`.
- Current blocker: none
- Next exact step: Commit the focused fix and journal update on `codex/issue-430`.
- Verification gap: Full suite not run; verification is limited to focused Phase 20 request creation, delegation, reconciliation, and validation tests.
- Files touched: `control-plane/aegisops_control_plane/service.py`; `control-plane/tests/test_service_persistence.py`; `.codex-supervisor/issues/430/issue-journal.md`
- Rollback concern: Low. The change only narrows reviewed action-request reuse by requester identity; same-requester duplicate reuse remains covered by the existing test.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_delegates_approved_low_risk_action_through_shuffle_adapter control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_rejects_shuffle_delegation_when_payload_binding_drifts control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_shuffle_run_back_into_authoritative_action_execution control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciliation_fail_closes_when_downstream_run_identity_drifts`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Reproducer command: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_keeps_requester_identity_inside_reviewed_action_request_deduplication control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reuses_reviewed_action_request_for_matching_idempotency_key`
- Reproduced failure before fix: second call from `analyst-002` returned the first action request ID.
