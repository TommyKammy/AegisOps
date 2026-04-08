# Issue #301: implementation: extend asset, identity, and privilege context for identity-centric analytic signals and alerts

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/301
- Branch: codex/issue-301
- Workspace: .
- Journal: .codex-supervisor/issues/301/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 7 (implementation=1, repair=6)
- Last head SHA: e08d03b122a21f5ea3688b1be195048f613a0af3
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-08T14:40:01.640Z

## Latest Codex Summary
`_attach_native_detection_context()` now persists a linked case when reviewed context changes, even if the evidence ID set is unchanged. The repeated native-link regression now verifies the case record advances from a second native ingest that reuses the same evidence ID but adds new reviewed identity/privilege context.

Summary: Persisted native-linked cases on reviewed-context-only updates and added a repeated native-link regression for the stale-case path.
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_preserves_reviewed_context_when_native_detection_links_existing_case control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_extends_promoted_wazuh_alert_with_existing_case_linkage`; `bash scripts/test-verify-asset-identity-privilege-context-baseline.sh`; `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection`
Next action: commit the repair and refresh local review on the updated branch head
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: native-linked cases must be re-persisted when merged reviewed context changes, even if the repeated native ingest reuses the same evidence ID.
- What changed: `_attach_native_detection_context()` now persists case updates on reviewed-context-only deltas, and the repeated native-link test exercises the same evidence ID path with a follow-up identity/privilege context update.
- Current blocker: none.
- Next exact step: commit the repair, then refresh local review on the new branch head.
- Verification gap: none for the scoped repair; the baseline verifier and the relevant unittest modules passed on this turn.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`.
- Rollback concern: case persistence should stay tied to reviewed-context merges without changing the existing evidence-linking behavior.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
