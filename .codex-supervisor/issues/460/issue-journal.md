# Issue #460: implementation: introduce shared control-plane test-support utilities and fake-store helpers

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/460
- Branch: codex/issue-460
- Workspace: .
- Journal: .codex-supervisor/issues/460/issue-journal.md
- Current phase: addressing_review
- Attempt count: 4 (implementation=1, repair=1)
- Last head SHA: c7321310b80d9e48d3a296723dfa14aa2c49f744
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc56t82A|PRRT_kwDOR2iDUc56t82F|PRRT_kwDOR2iDUc56t82H
- Repeated failure signature count: 1
- Updated at: 2026-04-14T05:46:29.926Z

## Latest Codex Summary
Applied the CodeRabbit review fix in [control-plane/tests/support/fake_store.py](control-plane/tests/support/fake_store.py) by adding per-instance locks and `_consume_mutation_token()` gates to the three one-shot mutation wrappers, so `mutate_once` cannot race and run twice under concurrent access. I added deterministic concurrency regression coverage in [control-plane/tests/test_support_package.py](control-plane/tests/test_support_package.py) that exercises the contested transaction, list/aggregate, and out-of-band paths.

Focused verification passed, the change is committed as `c732131` (`Fix fake store one-shot mutation races`), and `codex/issue-460` has been pushed to `origin` for PR #470. I updated the local issue journal working notes; I did not post or resolve the GitHub review thread.

Summary: Fixed the shared `fake_store` one-shot mutation race with lock-protected token consumption, added focused concurrent regression tests, committed as `c732131`, and pushed `codex/issue-460`.
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_support_package`; `python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness`; `python3 -m unittest control-plane.tests.test_service_persistence_ingest_case_lifecycle control-plane.tests.test_service_persistence_action_reconciliation`
Next action: Monitor PR #470 after commit `c732131` and, if desired, reply to or resolve the remaining CodeRabbit thread once the updated diff/check state is visible.
Failure signature: PRRT_kwDOR2iDUc56t82A|PRRT_kwDOR2iDUc56t82F|PRRT_kwDOR2iDUc56t82H

## Active Failure Context
- Category: review
- Summary: 3 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/470#discussion_r3077348217
- Details:
  - control-plane/tests/test_support_package.py:13 summary=_⚠️ Potential issue_ | _🟠 Major_ 🧩 Analysis chain 🌐 Web query: `In Python's import system, if a package named `support` is already present in `sys.modules`, will `from suppor... url=https://github.com/TommyKammy/AegisOps/pull/470#discussion_r3077348217
  - control-plane/tests/test_support_package.py:96 summary=_⚠️ Potential issue_ | _🟠 Major_ **Replace the fixed sleep with an explicit rendezvous.** `time.sleep(0.05)` does not guarantee the second thread has entered `inspect_readiness... url=https://github.com/TommyKammy/AegisOps/pull/470#discussion_r3077348223
  - control-plane/tests/test_support_package.py:124 summary=_⚠️ Potential issue_ | _🟠 Major_ **The shared transaction helper has the same timing hole.** This helper releases `mutate_once` after an arbitrary sleep, but it never proves th... url=https://github.com/TommyKammy/AegisOps/pull/470#discussion_r3077348225

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining blocker was the unresolved CodeRabbit feedback on `control-plane/tests/test_support_package.py`; the live test file still used a generic `support` import path and sleep-based thread coordination, so a focused test-only fix was still required.
- What changed: Updated `control-plane/tests/test_support_package.py` to load `control-plane/tests/support` through a unique importlib namespace instead of `from support...`, replaced the list/readiness sleep with an explicit `Event` from `_NoOpStore.inspect_readiness_aggregates()`, and changed the shared transaction helper to wait for both worker threads to reach the `store.transaction()` call boundary before releasing the blocked one-shot mutation.
- Current blocker: none
- Next exact step: Commit and push the focused `test_support_package.py` review fix to `codex/issue-460`, then leave PR #470 ready for manual thread resolution or comment reply if requested.
- Verification gap: none for the reviewed code paths after focused local unittest coverage.
- Files touched: `.codex-supervisor/issues/460/issue-journal.md`, `control-plane/tests/test_support_package.py`
- Rollback concern: Existing service-persistence tests import `_service_persistence_support` as a broad symbol bag, so compatibility re-exports there must stay intact until those consumers are narrowed intentionally.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence_ingest_case_lifecycle control-plane.tests.test_service_persistence_action_reconciliation`
### Scratchpad
- Initial reproducer failure: `ModuleNotFoundError: No module named 'support'` from `python3 -m unittest control-plane.tests.test_support_package`.
- Follow-up compatibility fixes restored `dataclass`, `secrets`, and `unittest` exports in `_service_persistence_support.py` and preserved `json` imports in Phase 19/21 workflow validation tests.
- CI repair reproducer: `python3 <redacted-local-path> --repo . --pr 470` showed the failing `verify` run died in `scripts/verify-phase-14-identity-rich-source-expansion-ci-validation.sh` with `Missing required Phase 14 unittest-discoverable test ... test_service_admits_github_audit_fixture_through_wazuh_source_profile`.
- Local repair proof: `bash scripts/verify-phase-14-identity-rich-source-expansion-ci-validation.sh`, `bash scripts/verify-phase-15-identity-grounded-analyst-assistant-boundary.sh`, `python3 -m unittest control-plane.tests.test_phase14_identity_rich_source_profile_docs control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence_ingest_case_lifecycle control-plane.tests.test_cli_inspection`, and `python3 -m unittest control-plane.tests.test_service_persistence_assistant_advisory control-plane.tests.test_service_persistence_action_reconciliation` all pass after restoring the AST-visible compatibility base.
- Review reproducer proof: `python3 -m unittest control-plane.tests.test_support_package`, `python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness`, and `python3 -m unittest control-plane.tests.test_service_persistence_ingest_case_lifecycle control-plane.tests.test_service_persistence_action_reconciliation` all pass after lock-protecting `mutate_once` token consumption in `control-plane/tests/support/fake_store.py`.
- Review follow-up proof: `python3 -m unittest control-plane.tests.test_support_package`, `python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness`, and `python3 -m unittest control-plane.tests.test_service_persistence_ingest_case_lifecycle control-plane.tests.test_service_persistence_action_reconciliation` all pass after replacing the generic `support` import with an importlib-loaded unique namespace and swapping both sleep-based rendezvous points for explicit `threading.Event` coordination in `control-plane/tests/test_support_package.py`.
