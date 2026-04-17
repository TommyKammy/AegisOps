# Issue #515: implementation: add the reviewed feedback loop from assistant output into AI Trace and Recommendation lifecycle

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/515
- Branch: codex/issue-515
- Workspace: .
- Journal: .codex-supervisor/issues/515/issue-journal.md
- Current phase: addressing_review
- Attempt count: 2 (implementation=1, repair=1)
- Last head SHA: 212faa8b870bfb4be38e36e8d5fe248804eebcae
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc57xWr_|PRRT_kwDOR2iDUc57xWsL|PRRT_kwDOR2iDUc57xWsR
- Repeated failure signature count: 1
- Updated at: 2026-04-17T15:07:10.956Z

## Latest Codex Summary
Implemented the Phase 24 feedback-loop slice in [service.py](control-plane/aegisops_control_plane/service.py) and added focused coverage in [test_phase24_live_assistant_feedback_loop_validation.py](control-plane/tests/test_phase24_live_assistant_feedback_loop_validation.py). `run_live_assistant_workflow` now persists reviewed assistant output into both `AITrace` and a linked `Recommendation`, carries stable source/output-contract linkage, and keeps unresolved provider outcomes auditable instead of dropping them as ephemeral text.

I reproduced the issue first with a narrow failing test, then fixed it and checkpointed the slice in commit `212faa8` (`Add Phase 24 assistant feedback loop persistence`). I also updated the local issue journal working notes.

Summary: Added Phase 24 live assistant feedback-loop persistence so assistant runs materialize linked `AITrace` and `Recommendation` review records, including unresolved outcomes.
State hint: implementing
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase24_live_assistant_feedback_loop_validation`; `python3 -m unittest control-plane.tests.test_service_persistence_assistant_advisory`
Next action: Run additional Phase 24 surface/provider/fallback validation suites or open/update a draft PR from commit `212faa8` if this slice should be reviewed now.
Failure signature: PRRT_kwDOR2iDUc57xWr_|PRRT_kwDOR2iDUc57xWsL|PRRT_kwDOR2iDUc57xWsR

## Active Failure Context
- Category: review
- Summary: 3 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/521#discussion_r3101275498
- Details:
  - control-plane/aegisops_control_plane/service.py:4922 summary=_⚠️ Potential issue_ | _🟠 Major_ **Persist the pre-provider unresolved branch too.** `_persist_live_assistant_feedback_loop()` is only reached on the post-provider path. url=https://github.com/TommyKammy/AegisOps/pull/521#discussion_r3101275498
  - control-plane/aegisops_control_plane/service.py:4935 summary=_⚠️ Potential issue_ | _🟠 Major_ 🧩 Analysis chain 🏁 Script executed: Repository: TommyKammy/AegisOps Length of output: 659 --- **Add missing type imports to resolve F821 erro... url=https://github.com/TommyKammy/AegisOps/pull/521#discussion_r3101275516
  - control-plane/tests/test_phase24_live_assistant_feedback_loop_validation.py:149 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Add a regression for the already-unresolved advisory path.** These tests cover provider success and provider failure, but not the branch wher... url=https://github.com/TommyKammy/AegisOps/pull/521#discussion_r3101275522

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining review-thread gap was narrower than the original slice: the already-unresolved advisory branch still returned before `_persist_live_assistant_feedback_loop`, and the new helper annotations referenced provider result types without importing them.
- What changed: Moved `reviewed_input_refs` construction ahead of the advisory readiness gate, persisted the pre-provider unresolved branch with `provider_result=None`, added the missing `AssistantProviderResult` and `AssistantProviderFailure` imports, and added a regression that proves an already-unresolved reviewed advisory still materializes linked `AITrace` and `Recommendation` records without calling the provider.
- Current blocker: None.
- Next exact step: Commit the review-fix delta, then push/update PR #521 so the unresolved automated threads can be re-reviewed.
- Verification gap: Focused unit coverage is green, including the fallback validation file for reviewed unresolved context; no broader full-suite run yet.
- Files touched: `control-plane/aegisops_control_plane/service.py`; `control-plane/tests/test_phase24_live_assistant_feedback_loop_validation.py`; `.codex-supervisor/issues/515/issue-journal.md`
- Rollback concern: Low to moderate; the change adds automatic recommendation materialization on every live assistant workflow call, so any callers assuming AI-trace-only persistence should be checked if broader Phase 24 tests expose coupling.
- Last focused commands: `python3 -m unittest control-plane.tests.test_phase24_live_assistant_feedback_loop_validation`; `python3 -m unittest control-plane.tests.test_phase24_live_assistant_fallback_validation`; `python3 -m unittest control-plane.tests.test_service_persistence_assistant_advisory`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
