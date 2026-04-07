# Issue #275: Follow-up: design: define the approved automation substrate contract and approval-binding model (#266) - The new automation substrate contract makes `delegation_id` a required delegation field and explicitly says later `Action Execution`...

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/275
- Branch: codex/issue-275
- Workspace: .
- Journal: .codex-supervisor/issues/275/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: a509baa0fbe6f9594bedbdb72b03b9138ac4f626
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-07T07:39:30.364Z

## Latest Codex Summary
- Reproduced the residual delegation-identity drift by adding a focused runtime test and a focused shared-doc test, then fixed reconciliation to carry `delegation_id` in `subject_linkage` and deterministic correlation keys after reviewed delegation.
- Aligned `docs/control-plane-state-model.md` and `docs/phase-13-guarded-automation-ci-validation.md` with the approved automation contract and verified the focused runtime/doc checks plus the control-plane and automation-contract guard scripts.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The residual finding is caused by `reconcile_action_execution()` preserving approval and action-request linkage but dropping emitted `delegation_id` from reconciliation `subject_linkage` and correlation keys, while the control-plane state model still omits delegation identity from the approved reconciliation baseline.
- What changed: Added a narrow failing runtime test and a narrow failing shared-doc test; updated `control-plane/aegisops_control_plane/service.py` so reconciliation records now preserve `delegation_ids` and correlation keys include `approval_decision_id` plus `delegation_id` once delegation exists; updated `docs/control-plane-state-model.md` and `docs/phase-13-guarded-automation-ci-validation.md` to keep the baseline and focused verification aligned.
- Current blocker: none
- Next exact step: Commit the verified fix on `codex/issue-275`; open/update a draft PR only if requested or if supervisor flow requires it next.
- Verification gap: Focused verification is green; broader full-suite or CI workflow execution was not run in this turn.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_wazuh_alert_ingest_contract_docs.py`, `docs/control-plane-state-model.md`, `docs/phase-13-guarded-automation-ci-validation.md`
- Rollback concern: Reconciliation correlation keys for action-execution records now include approval and delegation identity after delegation, so any consumers that assumed the older shorter key format would need to tolerate the expanded key.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_shuffle_run_back_into_authoritative_action_execution control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution control-plane.tests.test_wazuh_alert_ingest_contract_docs`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
