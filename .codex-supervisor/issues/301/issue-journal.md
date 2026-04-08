# Issue #301: implementation: extend asset, identity, and privilege context for identity-centric analytic signals and alerts

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/301
- Branch: codex/issue-301
- Workspace: .
- Journal: .codex-supervisor/issues/301/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 6 (implementation=1, repair=5)
- Last head SHA: 566bbffb729a5da1fd735a78e4be8ef9bf0efae3
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-08T14:33:21.707Z

## Latest Codex Summary
Summary: Merged the alert’s current reviewed context into native-detection case rewrites, added a regression for the promote-update-link sequence, and committed the fix as `566bbff`
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_merges_reviewed_context_for_existing_alert_updates control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_preserves_reviewed_context_when_native_detection_links_existing_case`; `bash scripts/test-verify-asset-identity-privilege-context-baseline.sh`; `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection`
Next action: refresh local review on branch head `566bbff`
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: the Wazuh native adapter must carry reviewed correlation context into `AnalyticSignalAdmission.reviewed_context` so the service can persist reviewed context on the alert and downstream case records.
- What changed: `wazuh.py` now populates `reviewed_context` from the adapter's reviewed correlation context; the adapter and persistence tests now assert the native-ingest path preserves that context.
- Current blocker: none.
- Next exact step: refresh local review on the updated branch head after the repair commit lands.
- Verification gap: none for the scoped repair; the baseline verifier and focused unit suites passed on this turn.
- Files touched: `control-plane/aegisops_control_plane/adapters/wazuh.py`, `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence.py`.
- Rollback concern: the native adapter's reviewed-context payload must stay aligned with the reviewed correlation context that the service records separately for reconciliation.
- Last focused command: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_wazuh_fixture_through_substrate_adapter_boundary control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_extends_promoted_wazuh_alert_with_existing_case_linkage`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
