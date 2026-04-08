# Issue #302: implementation: onboard GitHub audit signals through Wazuh-backed source profiles

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/302
- Branch: codex/issue-302
- Workspace: .
- Journal: .codex-supervisor/issues/302/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 5e3bb709f70842026eb9631b6d47d1ccb6679ec7
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-08T15:11:45.953Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: GitHub audit Wazuh alerts need a structured reviewed source profile, not just the generic flat Wazuh correlation context, so the control-plane can preserve accountable source identity, actor/target identity, repository context, and privilege-change metadata.
- What changed: Added a GitHub audit onboarding package doc, a representative Wazuh GitHub audit fixture, adapter logic to build a structured GitHub source profile, and service plumbing to persist that profile through alert, analytic-signal, and reconciliation records.
- Current blocker: None.
- Next exact step: Commit the GitHub audit source-profile slice on `codex/issue-302`.
- Verification gap: None for the focused slice; the mandated Wazuh adapter/service tests and the source-onboarding-contract verifier now pass.
- Files touched: `control-plane/aegisops_control_plane/adapters/wazuh.py`, `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_github_audit_source_profile_docs.py`, `control-plane/tests/fixtures/wazuh/github-audit-alert.json`, `docs/source-families/github-audit/onboarding-package.md`
- Rollback concern: The new GitHub-specific profile is additive and leaves the existing non-GitHub Wazuh fixtures/tests unchanged.
- Last focused command: `python3 -m unittest control-plane.tests.test_github_audit_source_profile_docs control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
