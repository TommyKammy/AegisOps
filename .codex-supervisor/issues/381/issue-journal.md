# Issue #381: implementation: make live substrate admission and replay-versus-live evidence capture work for the first source family

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/381
- Branch: codex/issue-381
- Workspace: .
- Journal: .codex-supervisor/issues/381/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 4715b7deeb1c546b3497779f2584c7c373c81fdd
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T22:30:33.132Z

## Latest Codex Summary
- Reproduced that GitHub-audit live Wazuh intake and fixture/native-record replay produced the same reviewed source profile without any admission marker, leaving replay-versus-live provenance ambiguous on the runtime path.
- Added focused persistence coverage for replay-versus-live admission provenance, then updated native-detection intake to stamp replay defaults, stamp live Wazuh webhook provenance, merge that provenance into reviewed context, and persist it into reconciliation subject linkage.
- Focused verification passed for the new provenance test, the GitHub/Microsoft 365/Entra reviewed-source-profile persistence tests, the trusted/untrusted live Wazuh ingress service tests, and existing restatement/case-linkage coverage.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue #381 was not blocked on first-family live admission itself; the missing behavior was provenance capture. Live `ingest_wazuh_alert()` already admitted reviewed GitHub-audit payloads, but replay/native-record intake and live webhook intake produced indistinguishable reviewed context and evidence linkage.
- What changed: Added a failing test for replay-versus-live provenance, then taught `AegisOpsControlPlaneService` to stamp native-detection admission provenance (`fixture_replay` vs `live_wazuh_webhook`), merge it into reviewed-context provenance, and persist it under reconciliation `subject_linkage["admission_provenance"]`. Updated reviewed-context expectations for replay-backed source-profile tests.
- Current blocker: none
- Next exact step: commit the provenance fix checkpoint on `codex/issue-381`, then consider whether to extend focused live-path verification to explicit dedupe/restatement behavior for GitHub-audit webhook intake.
- Verification gap: No end-to-end live webhook restatement/deduplication test exists yet; current verification relies on the shared ingest path plus existing upstream restatement/case-linkage tests.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/381/issue-journal.md`
- Rollback concern: The new admission provenance is merged into reviewed-context `provenance.*` for native-detection admission, so any callers or consumers that assumed the provenance block was source-native only may need to tolerate the added `admission_kind`/`admission_channel` keys.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_github_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_microsoft_365_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_entra_id_fixture_through_wazuh_source_profile control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_admits_non_loopback_wazuh_ingest_from_trusted_proxy_peer control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_rejects_non_loopback_wazuh_ingest_from_untrusted_proxy_peer`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Failure signature reproduced before fix: `KeyError: 'admission_channel'` from `test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance`
