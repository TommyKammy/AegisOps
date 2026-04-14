# Issue #458: implementation: isolate the current Phase 19 live-slice policy checks behind reusable reviewed-slice policy logic

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/458
- Branch: codex/issue-458
- Workspace: .
- Journal: .codex-supervisor/issues/458/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: c2ef907ddb11cefc74e5aafb194a41927f7a5caa
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-14T03:26:33.521Z

## Latest Codex Summary
- Extracted the Phase 19 reviewed live-slice checks into `control-plane/aegisops_control_plane/reviewed_slice_policy.py`, rewired assistant/advisory and action-request paths through generic reviewed-slice wrappers, and added a focused delegation test to pin the extraction boundary while preserving existing fail-closed behavior.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The Phase 19 operator/advisory gating can move behind a dedicated reviewed-slice policy object without changing current live Wazuh-backed scope decisions or fail-closed behavior.
- What changed: Added `reviewed_slice_policy.py`; service now owns a reusable `ReviewedSlicePolicy` and delegates reviewed operator-case and case-scoped advisory checks through generic reviewed-slice wrappers; assistant context and execution coordinator call the generic reviewed-slice hooks; added a narrow service test that asserts the reusable policy object is the enforcement boundary; preserved the existing `Phase 19 ... live slice` error text after the first focused run exposed that compatibility requirement.
- Current blocker: none.
- Next exact step: Commit the verified extraction on `codex/issue-458`; if requested later, open a draft PR from this checkpoint.
- Verification gap: No additional manual verification run beyond the covered automated fail-closed workflow cases.
- Files touched: `control-plane/aegisops_control_plane/reviewed_slice_policy.py`, `control-plane/aegisops_control_plane/service.py`, `control-plane/aegisops_control_plane/assistant_context.py`, `control-plane/aegisops_control_plane/execution_coordinator.py`, `control-plane/tests/test_service_persistence.py`.
- Rollback concern: Low; the main risk is accidental drift in error wording or reviewed-slice gating if future changes bypass the new policy wrappers.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_phase19_operator_workflow_validation`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
