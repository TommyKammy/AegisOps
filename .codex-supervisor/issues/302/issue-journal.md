# Issue #302: implementation: onboard GitHub audit signals through Wazuh-backed source profiles

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/302
- Branch: codex/issue-302
- Workspace: .
- Journal: .codex-supervisor/issues/302/issue-journal.md
- Current phase: addressing_review
- Attempt count: 3 (implementation=1, repair=2)
- Last head SHA: 8bf5f5993efeec78b9607dbab7fcd2c2fe806ba2
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc55m8sR|PRRT_kwDOR2iDUc55m8sf
- Repeated failure signature count: 1
- Updated at: 2026-04-08T15:41:16.210Z

## Latest Codex Summary
Applied the remaining review fixes in [control-plane/aegisops_control_plane/adapters/wazuh.py](control-plane/aegisops_control_plane/adapters/wazuh.py#L37) by adding `actor.login` / `target.login` to reviewed correlation fields and gating the reviewed source-profile builder to the GitHub audit family. Added regressions in [control-plane/tests/test_wazuh_adapter.py](control-plane/tests/test_wazuh_adapter.py#L202) for the sparse GitHub source-family path, the login-only identity path, and the non-GitHub family rejection path. The review-fix commits were pushed as `4c0ec61` and `a42ab87`.

Summary: `WazuhAlertAdapter` now preserves login-only GitHub audit identities in the correlation key and no longer applies GitHub defaults to non-GitHub families
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence`; `bash scripts/test-verify-source-onboarding-contract-doc.sh`
Next action: Await GitHub/CodeRabbit refresh or manual resolution for the remaining unresolved thread on `control-plane/aegisops_control_plane/adapters/wazuh.py`
Failure signature: PRRT_kwDOR2iDUc55m8sR|PRRT_kwDOR2iDUc55m8sf

## Active Failure Context
- Category: review
- Summary: 2 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/309#discussion_r3052484560
- Details:
  - control-plane/aegisops_control_plane/adapters/wazuh.py:54 summary=_⚠️ Potential issue_ | _🟠 Major_ **Add `actor.login` / `target.login` to the correlation fields.** Lines 318-320 already treat `login` as the fallback identity, but Lines 47-50... url=https://github.com/TommyKammy/AegisOps/pull/309#discussion_r3052484560
  - control-plane/aegisops_control_plane/adapters/wazuh.py:269 summary=_⚠️ Potential issue_ | _🟠 Major_ **Gate this builder to the GitHub family before applying GitHub defaults.** Lines 253 and 262-269 make any non-empty `data.source_family` enoug... url=https://github.com/TommyKammy/AegisOps/pull/309#discussion_r3052484579

## Codex Working Notes
### Current Handoff
- Hypothesis: GitHub audit Wazuh alerts need a structured reviewed source profile, not just the generic flat Wazuh correlation context, so the control-plane can preserve accountable source identity, actor/target identity, repository context, privilege-change metadata, and login-only identity fallbacks without broadening to unrelated families.
- What changed: Added `actor.login` / `target.login` to reviewed correlation fields, gated GitHub defaults to the approved family, and added regressions for sparse GitHub, login-only GitHub, and non-GitHub alerts.
- Current blocker: None.
- Next exact step: Wait for GitHub/CodeRabbit to clear the remaining unresolved thread or get manual resolution guidance.
- Verification gap: None for the focused slice; the Wazuh adapter/service tests and the source-onboarding-contract verifier now pass.
- Files touched: `control-plane/aegisops_control_plane/adapters/wazuh.py`, `control-plane/tests/test_wazuh_adapter.py`, `.codex-supervisor/issues/302/issue-journal.md`
- Rollback concern: The new GitHub-specific profile is additive and leaves the existing non-GitHub Wazuh fixtures/tests unchanged.
- Last focused command:
- Last focused commands: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence`; `bash scripts/test-verify-source-onboarding-contract-doc.sh`; `fetch_comments.py`-based thread-state check via `gh api graphql`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
