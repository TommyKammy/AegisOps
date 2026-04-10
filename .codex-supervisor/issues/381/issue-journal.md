# Issue #381: implementation: make live substrate admission and replay-versus-live evidence capture work for the first source family

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/381
- Branch: codex/issue-381
- Workspace: .
- Journal: .codex-supervisor/issues/381/issue-journal.md
- Current phase: stabilizing
- Attempt count: 3 (implementation=3, repair=0)
- Last head SHA: 9d9d1567ab8ddba86eabb6f1b91cf377f0f2d41e
- Blocked reason: none
- Last failure signature: stale-stabilizing-no-pr-recovery-loop
- Repeated failure signature count: 0
- Updated at: 2026-04-10T22:50:47Z

## Latest Codex Summary
Published the existing issue branch state for review, then fixed the first CI regression exposed by PR `#386`. The failing `verify` job showed that `test_service_admits_wazuh_fixture_through_substrate_adapter_boundary` still expected the pre-provenance reviewed context. I updated that legacy assertion to include explicit replay admission provenance in both reviewed context and reconciliation linkage.

Verification run:
`python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_github_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_restates_and_deduplicates_live_wazuh_github_audit_ingest_with_case_linkage control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_microsoft_365_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_entra_id_fixture_through_wazuh_source_profile control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_admits_non_loopback_wazuh_ingest_from_trusted_proxy_peer control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_rejects_non_loopback_wazuh_ingest_from_untrusted_proxy_peer`
`python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_wazuh_fixture_through_substrate_adapter_boundary`
`bash scripts/verify-phase-11-control-plane-ci-validation.sh`

Publish notes:
- `git push -u origin codex/issue-381`
- GitHub app PR creation returned `403 Resource not accessible by integration`
- fallback succeeded with `gh pr create --draft --base main --head codex/issue-381 --title "[codex] Preserve live-vs-replay Wazuh admission provenance" --body-file <tempfile>`
- `gh pr checks 386` showed `verify` failing in `Run Phase 11 control-plane validation`

Summary: Opened draft PR #386, reproduced the failing CI expectation locally, and fixed the stale substrate-boundary test to match the new replay provenance contract
State hint: repairing_ci
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_github_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_restates_and_deduplicates_live_wazuh_github_audit_ingest_with_case_linkage control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_microsoft_365_audit_fixture_through_wazuh_source_profile control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_entra_id_fixture_through_wazuh_source_profile control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_admits_non_loopback_wazuh_ingest_from_trusted_proxy_peer control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_service_rejects_non_loopback_wazuh_ingest_from_untrusted_proxy_peer`; `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_wazuh_fixture_through_substrate_adapter_boundary`; `bash scripts/verify-phase-11-control-plane-ci-validation.sh`
Failure signature: ci-stale-replay-provenance-expectation

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue #381 was not blocked on first-family live admission itself; the missing behavior was provenance capture. Live `ingest_wazuh_alert()` already admitted reviewed GitHub-audit payloads, but replay/native-record intake and live webhook intake produced indistinguishable reviewed context and evidence linkage.
- What changed: The branch now contains the provenance merge in `service.py` plus focused regression coverage proving replay-vs-live distinction, reviewed runtime-path preservation, and case-linked live restatement/deduplication for the approved GitHub-audit family. This turn pushed `codex/issue-381`, opened draft PR `#386`, reproduced the failing `verify` job locally, and updated the older Wazuh substrate-boundary test so it asserts the explicit replay provenance contract instead of the pre-fix reviewed context.
- Current blocker: none
- Next exact step: commit the CI expectation fix, push it to `codex/issue-381`, and confirm PR `#386` requeues green or identify any remaining failing checks.
- Verification gap: No broader end-to-end HTTP runtime scenario was added this turn; coverage remains at service-level persistence plus the existing trusted/untrusted live-ingest service checks.
- Files touched: `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/381/issue-journal.md`
- Rollback concern: The new admission provenance is merged into reviewed-context `provenance.*` for native-detection admission, so any callers or consumers that assumed the provenance block was source-native only may need to tolerate the added `admission_kind`/`admission_channel` keys.
- Last focused command: `bash scripts/verify-phase-11-control-plane-ci-validation.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Failure signature reproduced before fix: `KeyError: 'admission_channel'` from `test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance`
- CI failure reproduced from PR `#386`: `test_service_admits_wazuh_fixture_through_substrate_adapter_boundary` still expected the old reviewed context without replay provenance
