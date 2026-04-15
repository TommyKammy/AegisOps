# Issue #480: implementation: add handoff and manual-fallback runtime visibility for after-hours and unresolved action states

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/480
- Branch: codex/issue-480
- Workspace: .
- Journal: .codex-supervisor/issues/480/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 4 (implementation=1, repair=3)
- Last head SHA: a9444602c136d7fbeec3a7da59e551b69a81528c
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-15T00:53:47.318Z

## Latest Codex Summary
Implemented the local-review repair in commit `a944460` (`Add governed action-review visibility writers`).

The fix adds explicit governed write surfaces for action-review `manual_fallback` and `escalation` visibility in the service, CLI, and HTTP operator API, and stores them on the authoritative reviewed record for that request’s scope: case when present, otherwise alert. I also updated the runtime-visibility read path to fall back to alert reviewed context for alert-scoped requests, and gated `after_hours_handoff` off terminal review states so historical completed/rejected/superseded chains stop inheriting the active handoff block.

Focused coverage now uses the supported write path instead of raw `persist_record(replace(... reviewed_context=...))`, and adds regressions for alert-scoped visibility plus suppressing handoff visibility on completed review history. The issue journal’s Codex Working Notes section was updated locally before closing the turn.

Summary: Added governed action-review visibility writers, fixed alert-scoped runtime visibility fallback, and prevented after-hours handoff from bleeding into historical terminal review chains
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase19_operator_workflow_validation control-plane.tests.test_service_persistence_restore_readiness control-plane.tests.test_cli_inspection`
Next action: Run a fresh local review on commit `a944460` to verify the three saved findings are cleared
Failure signature: none

## Active Failure Context
- Category: blocked
- Summary: Local review found 5 actionable finding(s) across 5 root cause(s); max severity=high; verified high-severity findings=2; verified max severity=high.
- Details:
  - findings=5
  - root_causes=5
  - summary=<redacted-local-path>

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining blocked findings were the missing approval gate on manual fallback plus record-fidelity gaps in escalation-note visibility; a narrow repair should enforce approved post-approval fallback writes and make escalation visibility depend on a stored note with actor/state snapshots.
- What changed: Tightened `record_action_review_manual_fallback()` to require an approved decision and reject pending/rejected/expired/superseded chains, and mirrored that guard in the manual-fallback read path so stale bad context cannot render. Made escalation visibility record-driven by requiring stored reviewed-context lineage, persisting `escalated_by_identity` and `review_state` at note time, and returning those stored values instead of synthesizing note visibility from `requested_payload["escalation_reason"]`. Wired the reviewed reverse-proxy HTTP route and CLI command to require/pass `escalated_by_identity`, and updated focused regressions for pending/rejected fallback rejection, stored escalation actor/state fidelity, no-note/no-visibility behavior, and reverse-proxy identity enforcement.
- Current blocker: none
- Next exact step: Commit this repair checkpoint and run a fresh local review against the new head to verify the five saved findings are cleared.
- Verification gap: None in the focused issue slice; the new approval/state and escalation-fidelity regressions pass in the standard issue verification slice.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/aegisops_control_plane/cli.py`, `control-plane/aegisops_control_plane/http_surface.py`, `control-plane/tests/test_cli_inspection.py`, `control-plane/tests/test_phase19_operator_workflow_validation.py`, `control-plane/tests/test_service_persistence_restore_readiness.py`
- Rollback concern: Low to medium. The repair narrows writer acceptance and changes escalation-note payload requirements, so any rollback would need to preserve the new `escalated_by_identity` / `review_state` expectations in CLI and HTTP callers.
- Last focused command: `python3 -m unittest control-plane.tests.test_phase19_operator_workflow_validation control-plane.tests.test_service_persistence_restore_readiness control-plane.tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Added regressions for pending/rejected manual fallback rejection, record-driven escalation visibility, escalation actor/state rendering, and reviewed reverse-proxy escalation identity enforcement.
