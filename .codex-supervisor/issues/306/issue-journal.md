# Issue #306: validation: add cross-source signal-quality and false-positive review coverage

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/306
- Branch: codex/issue-306
- Workspace: .
- Journal: .codex-supervisor/issues/306/issue-journal.md
- Current phase: addressing_review
- Attempt count: 4 (implementation=1, repair=1)
- Last head SHA: 0131ad49c50bca58b1e91091176e3e31ff5db6f1
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc55pZY8
- Repeated failure signature count: 1
- Updated at: 2026-04-08T18:25:25.654Z

## Latest Codex Summary
Summary: Fixed the Phase 14 negative-fixture harness, committed as `0131ad4`, and pushed `codex/issue-306`; PR `#313` now has a fresh `verify` run queued.
State hint: waiting_ci
Blocked reason: none
Tests: `bash -n scripts/test-verify-phase-14-identity-rich-source-expansion-ci-validation.sh`; `bash scripts/verify-phase-14-identity-rich-source-expansion-ci-validation.sh`; `bash scripts/test-verify-phase-14-identity-rich-source-expansion-ci-validation.sh`; `bash scripts/test-verify-ci-phase-14-workflow-coverage.sh`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`; `gh pr checks 313` now shows `verify` pending on run `24151191925`
Next action: monitor PR `#313` verify run `24151191925` to completion
Failure signature: PRRT_kwDOR2iDUc55pZY8

## Active Failure Context
- Category: review
- Summary: 1 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/313#discussion_r3053340014
- Details:
  - scripts/test-verify-phase-14-identity-rich-source-expansion-ci-validation.sh:115 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Pin the expected stderr line exactly.** The verifier emits single-line diagnostics in `scripts/verify-phase-14-identity-rich-source-expansion... url=https://github.com/TommyKammy/AegisOps/pull/313#discussion_r3053340014

## Codex Working Notes
### Current Handoff
- Hypothesis: the review thread is valid because the helper still allowed prefix matches on stderr, so the missing-validation fixture could pass without proving the exact single-line diagnostic.
- What changed: Tightened `assert_fails_with` in `scripts/test-verify-phase-14-identity-rich-source-expansion-ci-validation.sh` to use `grep -Fqx` and updated the missing-validation fixture to assert the full path-qualified stderr line.
- Current blocker: None.
- Next exact step: commit the review fix on `codex/issue-306` and publish the updated branch state.
- Verification gap: None for the review fix; `bash -n scripts/test-verify-phase-14-identity-rich-source-expansion-ci-validation.sh`, `bash scripts/test-verify-phase-14-identity-rich-source-expansion-ci-validation.sh`, and `bash scripts/verify-phase-14-identity-rich-source-expansion-ci-validation.sh /Users/jp.infra/Dev/AegisOps-worktrees/issue-306` all passed.
- Files touched: `scripts/test-verify-phase-14-identity-rich-source-expansion-ci-validation.sh`
- Rollback concern: Low; the change is isolated to the Phase 14 shell test harness and only narrows the assertion.
- Last focused command: `bash scripts/verify-phase-14-identity-rich-source-expansion-ci-validation.sh /Users/jp.infra/Dev/AegisOps-worktrees/issue-306`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
