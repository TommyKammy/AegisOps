# Issue #381: implementation: make live substrate admission and replay-versus-live evidence capture work for the first source family

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/381
- Branch: codex/issue-381
- Workspace: .
- Journal: .codex-supervisor/issues/381/issue-journal.md
- Current phase: addressing_review
- Attempt count: 4 (implementation=3, repair=1)
- Last head SHA: 23103806f6566565b2245848f2a0263f0012c7fc
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc56QSw1|PRRT_kwDOR2iDUc56QSw5
- Repeated failure signature count: 1
- Updated at: 2026-04-10T23:01:43.197Z

## Latest Codex Summary
Draft PR is open at `https://github.com/TommyKammy/AegisOps/pull/386` on `codex/issue-381`. After opening it, CI exposed one stale test expectation: [control-plane/tests/test_service_persistence.py](control-plane/tests/test_service_persistence.py) still expected the old Wazuh reviewed context without replay admission provenance. I fixed that assertion to match the new contract and pushed commit `2310380` (`Fix Wazuh provenance CI expectation`).

Local verification passed with the targeted regression and the repo’s CI-equivalent Phase 11 script:
- `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_github_audit_fixture_through_substrate_adapter_boundary`
- `bash scripts/verify-phase-11-control-plane-ci-validation.sh`

The issue journal was updated in [.codex-supervisor/issues/381/issue-journal.md](.codex-supervisor/issues/381/issue-journal.md). Current PR status shows `verify` requeued and `IN_PROGRESS` on head `23103806f6566565b2245848f2a0263f0012c7fc`.

Summary: Opened draft PR #386, fixed the CI-revealed stale Wazuh replay-provenance test expectation, and pushed commit `2310380`
State hint: waiting_ci
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_admits_github_audit_fixture_through_substrate_adapter_boundary`; `bash scripts/verify-phase-11-control-plane-ci-validation.sh`; earlier focused Wazuh provenance/runtime tests also passed
Next action: Monitor PR #386 `verify` completion and address any remaining CI or review feedback without broadening scope
Failure signature: PRRT_kwDOR2iDUc56QSw1|PRRT_kwDOR2iDUc56QSw5

## Active Failure Context
- Category: review
- Summary: 2 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/386#discussion_r3067075914
- Details:
  - control-plane/aegisops_control_plane/service.py:486 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Normalize provenance values after trimming whitespace.** Validation uses `strip()`, but the stored value keeps original whitespace. url=https://github.com/TommyKammy/AegisOps/pull/386#discussion_r3067075914
  - control-plane/tests/test_service_persistence.py:2818 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Assert `admission_kind` in live reviewed context as well.** These checks only pin `provenance.admission_channel` on the live path. url=https://github.com/TommyKammy/AegisOps/pull/386#discussion_r3067075919

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue #381 was not blocked on first-family live admission itself; the missing behavior was provenance capture. Live `ingest_wazuh_alert()` already admitted reviewed GitHub-audit payloads, but replay/native-record intake and live webhook intake produced indistinguishable reviewed context and evidence linkage.
- What changed: The branch now also trims stored `admission_provenance` values in `_normalize_admission_provenance()` so reviewed-context provenance and reconciliation linkage cannot retain stray whitespace, and the Wazuh runtime-path persistence tests now assert `admission_kind` alongside `admission_channel` for replay, live, restated, deduplicated, and case-linked reviewed context. A focused native-admission regression was added to prove whitespace-normalized provenance persists consistently into both reviewed context and reconciliation linkage.
- Current blocker: none
- Next exact step: commit and push the local review-thread fixes on `codex/issue-381`, then confirm PR `#386` clears the two remaining CodeRabbit threads and stays green.
- Verification gap: No broader end-to-end HTTP runtime scenario was added this turn; coverage remains at service-level persistence plus the existing trusted/untrusted live-ingest service checks.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `.codex-supervisor/issues/381/issue-journal.md`
- Rollback concern: The new admission provenance is merged into reviewed-context `provenance.*` for native-detection admission, so any callers or consumers that assumed the provenance block was source-native only may need to tolerate the added `admission_kind`/`admission_channel` keys.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_trims_native_admission_provenance_before_persisting_reviewed_context`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Failure signature reproduced before fix: `KeyError: 'admission_channel'` from `test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance`
- CI failure reproduced from PR `#386`: `test_service_admits_wazuh_fixture_through_substrate_adapter_boundary` still expected the old reviewed context without replay provenance
- Review fixes verified locally:
  - `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance`
  - `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_restates_and_deduplicates_live_wazuh_github_audit_ingest_with_case_linkage`
  - `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_trims_native_admission_provenance_before_persisting_reviewed_context`
