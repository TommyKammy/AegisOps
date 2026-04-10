# Issue #381: implementation: make live substrate admission and replay-versus-live evidence capture work for the first source family

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/381
- Branch: codex/issue-381
- Workspace: .
- Journal: .codex-supervisor/issues/381/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: e7801be93ccfcebd74cec073f729683586bbf374
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T22:38:53.899Z

## Latest Codex Summary
Extended the focused provenance checkpoint with explicit live webhook persistence coverage for the approved GitHub-audit family. The branch now proves that live `ingest_wazuh_alert()` keeps `live_wazuh_webhook` / `live` provenance visible while restatements mint a new analytic signal for the new substrate detection record, preserve the existing alert and case linkage, and exact repeats deduplicate on the reviewed runtime path.

The implementation remains in [service.py](control-plane/aegisops_control_plane/service.py); this turn tightened [test_service_persistence.py](control-plane/tests/test_service_persistence.py) and reran the adjacent live-ingest checks.

Summary: Added focused live GitHub-audit restatement and deduplication persistence coverage on top of the live-vs-replay Wazuh admission provenance fix.
State hint: stabilizing
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_restates_and_deduplicates_live_wazuh_github_audit_ingest_with_case_linkage control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_extends_promoted_wazuh_alert_with_existing_case_linkage`; `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_github_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_restates_and_deduplicates_live_wazuh_github_audit_ingest_with_case_linkage control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_microsoft_365_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_entra_id_fixture_through_wazuh_source_profile control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_admits_non_loopback_wazuh_ingest_from_trusted_proxy_peer control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_rejects_non_loopback_wazuh_ingest_from_untrusted_proxy_peer`; `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_extends_promoted_wazuh_alert_with_existing_case_linkage control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_upserts_alert_lifecycle_from_upstream_signals`
Next action: commit the live restatement/deduplication coverage checkpoint and, if a PR is opened next, summarize the reviewed runtime-path guarantees now covered
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue #381 was not blocked on first-family live admission itself; the missing behavior was provenance capture. Live `ingest_wazuh_alert()` already admitted reviewed GitHub-audit payloads, but replay/native-record intake and live webhook intake produced indistinguishable reviewed context and evidence linkage.
- What changed: Added a focused live-path persistence test for GitHub-audit webhook intake that creates, promotes, restates, and deduplicates the same reviewed incident. The test asserts that live provenance remains visible, restatements add a second substrate detection record and analytic signal under the same alert/case, and exact repeats deduplicate without collapsing live lineage.
- Current blocker: none
- Next exact step: commit the test-only checkpoint on `codex/issue-381` so the branch captures the new live restatement/deduplication guarantee in a reviewable state.
- Verification gap: No broader end-to-end HTTP runtime scenario was added this turn; coverage remains at service-level persistence plus the existing trusted/untrusted live-ingest service checks.
- Files touched: `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/381/issue-journal.md`
- Rollback concern: The new admission provenance is merged into reviewed-context `provenance.*` for native-detection admission, so any callers or consumers that assumed the provenance block was source-native only may need to tolerate the added `admission_kind`/`admission_channel` keys.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_github_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_restates_and_deduplicates_live_wazuh_github_audit_ingest_with_case_linkage control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_microsoft_365_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_entra_id_fixture_through_wazuh_source_profile control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_admits_non_loopback_wazuh_ingest_from_trusted_proxy_peer control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_rejects_non_loopback_wazuh_ingest_from_untrusted_proxy_peer`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Failure signature reproduced before fix: `KeyError: 'admission_channel'` from `test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance`
