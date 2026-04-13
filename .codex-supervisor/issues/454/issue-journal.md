# Issue #454: cleanup: remove duplicated low-level validators and normalize shared helper placement in service.py

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/454
- Branch: codex/issue-454
- Workspace: .
- Journal: .codex-supervisor/issues/454/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 4803547f05ff7aa16a89c81d6855229b82abaf6e
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-13T23:44:14.636Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: `control-plane/aegisops_control_plane/service.py` still contains duplicated low-level helper definitions and near-duplicate loopback/trusted-peer helpers that can be consolidated without changing runtime auth semantics.
- What changed: Added a focused source-layout regression test for `_require_non_empty_string`, removed the duplicate `_require_non_empty_string` definition, renamed the listener loopback helper to `_listener_is_loopback`, and centralized trusted-peer CIDR evaluation in `_is_trusted_peer_for_proxy_cidrs(...)`.
- Current blocker: none
- Next exact step: Review diff and continue with supervisor-directed follow-up if any new cleanup or review feedback appears.
- Verification gap: none for the requested local suites; no PR/CI checks were available in this turn.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`
- Rollback concern: Low; the shared trusted-peer helper is used by both protected-surface and Wazuh-ingest auth paths, so any rollback should preserve the current per-surface CIDR selection.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection control-plane.tests.test_phase21_runtime_auth_validation`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
