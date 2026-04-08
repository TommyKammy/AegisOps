# Issue #302: implementation: onboard GitHub audit signals through Wazuh-backed source profiles

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/302
- Branch: codex/issue-302
- Workspace: .
- Journal: .codex-supervisor/issues/302/issue-journal.md
- Current phase: addressing_review
- Attempt count: 3 (implementation=1, repair=2)
- Last head SHA: d6a258d246e5de5b2a28444c8127b64728fa98c0
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc55mw_I
- Repeated failure signature count: 1
- Updated at: 2026-04-08T15:31:09.300Z

## Latest Codex Summary
Summary: Kept the GitHub audit Wazuh source-profile path intact and fixed the sparse-alert gate so `data.source_family` alone still emits a reviewed source profile.
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence`; `bash scripts/test-verify-source-onboarding-contract-doc.sh`
Next action: Commit the sparse GitHub-audit review fix on `codex/issue-302` and update PR `#309`
Failure signature: PRRT_kwDOR2iDUc55mw_I

## Active Failure Context
- Category: review
- Summary: sparse GitHub audit alerts now retain reviewed source profiles when `data.source_family` is the only GitHub-specific field.
- Reference: https://github.com/TommyKammy/AegisOps/pull/309#discussion_r3052420569
- Details:
  - control-plane/aegisops_control_plane/adapters/wazuh.py:249 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Don't drop sparse GitHub audit alerts just because entity fields are missing.** Line 242 reads `data.source_family`, but Lines 244-249 ignore... url=https://github.com/TommyKammy/AegisOps/pull/309#discussion_r3052420569

## Codex Working Notes
### Current Handoff
- Hypothesis: GitHub audit Wazuh alerts need a structured reviewed source profile, not just the generic flat Wazuh correlation context, so the control-plane can preserve accountable source identity, actor/target identity, repository context, and privilege-change metadata, even when entity details are sparse.
- What changed: Added a sparse-alert regression test and updated the GitHub audit profile gate so `data.source_family` alone still emits `reviewed_source_profile`.
- Current blocker: None.
- Next exact step: Commit the review fix on `codex/issue-302` and update PR `#309`.
- Verification gap: None for the focused slice; the Wazuh adapter/service tests and the source-onboarding-contract verifier now pass.
- Files touched: `control-plane/aegisops_control_plane/adapters/wazuh.py`, `control-plane/tests/test_wazuh_adapter.py`, `.codex-supervisor/issues/302/issue-journal.md`
- Rollback concern: The new GitHub-specific profile is additive and leaves the existing non-GitHub Wazuh fixtures/tests unchanged.
- Last focused commands: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence`; `bash scripts/test-verify-source-onboarding-contract-doc.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
