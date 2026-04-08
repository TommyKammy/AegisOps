# Issue #302: implementation: onboard GitHub audit signals through Wazuh-backed source profiles

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/302
- Branch: codex/issue-302
- Workspace: .
- Journal: .codex-supervisor/issues/302/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 5 (implementation=1, repair=4)
- Last head SHA: 708f8402edc3f063d7cc8b98f54f23ebf59470a5
- Blocked reason: none
- Last failure signature: local-review:unknown:none:0:0:clean
- Repeated failure signature count: 3
- Updated at: 2026-04-08T15:53:31Z

## Latest Codex Summary
Summary: Tightened `_build_reviewed_source_profile()` so only alerts with an explicit `data.source_family == "github_audit"` can emit the reviewed GitHub profile, and added a regression for GitHub-shaped payloads missing the family marker. Focused adapter and persistence tests plus the onboarding contract verifier passed.
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence`; `bash scripts/test-verify-source-onboarding-contract-doc.sh`
Next action: Commit the review fix and await the next local review pass
Failure signature: local-review:unknown:none:0:0:clean

## Active Failure Context
- Category: blocked
- Summary: Local review found 2 actionable finding(s) across 2 root cause(s); max severity=medium; verified high-severity findings=0; verified max severity=none.
- Details:
  - findings=2
  - root_causes=2
  - summary=<redacted-local-path>

## Codex Working Notes
### Current Handoff
- Hypothesis: the reviewed GitHub audit profile path must require an explicit `data.source_family` marker, otherwise GitHub-shaped Wazuh payloads can be misclassified into the approved family.
- What changed: `_build_reviewed_source_profile()` now returns `None` unless `data.source_family == "github_audit"`, and the adapter test suite now includes a regression for missing-family GitHub-shaped payloads.
- Current blocker: None.
- Next exact step: Commit the review fix, then wait for the next local review pass.
- Verification gap: None for the focused slice; the Wazuh adapter/service tests and the source-onboarding-contract verifier now pass.
- Files touched: `control-plane/aegisops_control_plane/adapters/wazuh.py`, `control-plane/tests/test_wazuh_adapter.py`, `.codex-supervisor/issues/302/issue-journal.md`
- Rollback concern: The sparse approved GitHub audit case still passes because it includes the explicit family marker.
- Last focused commands: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence`; `bash scripts/test-verify-source-onboarding-contract-doc.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
