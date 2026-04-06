# Issue #260: implementation: add reviewed case-promotion behavior for Wazuh-driven alerts

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/260
- Branch: codex/issue-260
- Workspace: .
- Journal: .codex-supervisor/issues/260/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 0a43304f7635cc840621a512c65f824554cb9232
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-06T22:34:54.763Z

## Latest Codex Summary
- Added a reviewed `promote_alert_to_case` service path for Wazuh-driven alerts so case creation/update, alert escalation, analytic-signal linkage, evidence linkage, and reconciliation linkage all happen inside the control-plane flow instead of relying on manually preseeded `CaseRecord` state.
- Tightened the Wazuh restatement and analyst-queue tests to reproduce the missing promotion entrypoint first, then verified the implementation against the requested unittest targets and the Wazuh contract doc tests.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The missing behavior was a service-owned reviewed promotion path; ingest could preserve an existing `case_id`, but nothing created or updated the durable `CaseRecord` and linked evidence/reconciliation state from Wazuh-driven alert handling.
- What changed: Added `AegisOpsControlPlaneService.promote_alert_to_case`, updated Wazuh persistence and CLI tests to use the service promotion path instead of manual preseeded case rows, and documented reviewed Wazuh case-promotion semantics in the control-plane state model and Wazuh ingest contract.
- Current blocker: none
- Next exact step: Commit the verified promotion-path changes on `codex/issue-260` as a coherent checkpoint.
- Verification gap: Did not run the full repository test suite outside the targeted control-plane and Wazuh contract checks.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_cli_inspection.py; docs/control-plane-state-model.md; docs/wazuh-alert-ingest-contract.md; .codex-supervisor/issues/260/issue-journal.md
- Rollback concern: The new promotion path updates evidence and reconciliation linkage for every reconciliation record tied to the promoted alert; if later review wants narrower historical mutation semantics, revisit `_link_case_to_alert_reconciliations`.
- Last focused command: python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection control-plane.tests.test_wazuh_alert_ingest_contract_docs
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
