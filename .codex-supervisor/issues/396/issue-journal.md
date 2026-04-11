# Issue #396: implementation: expose case detail, evidence provenance, reviewed context, and cited advisory output on the operator surface

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/396
- Branch: codex/issue-396
- Workspace: .
- Journal: .codex-supervisor/issues/396/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: b98252ac7de971944a385295618efea992bfaebf
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-11T22:00:51.761Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 19 operator coverage was missing a dedicated case-detail inspection path even though queue, alert detail, assistant context, and cited advisory views already existed.
- What changed: Added a failing CLI reproducer for `inspect-case-detail`, implemented `CaseDetailSnapshot` plus `inspect_case_detail()` by composing the existing reviewed assistant-context/advisory boundary, exposed the path in CLI and HTTP runtime routing, added HTTP coverage, and updated the control-plane README command list.
- Current blocker: none
- Next exact step: Commit the case-detail operator-surface slice, then continue with any remaining Phase 19 workflow alignment gaps outside the inspection surface if they appear in broader verification.
- Verification gap: Full `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'` has not been run yet this turn; focused operator-surface coverage passed.
- Files touched: .codex-supervisor/issues/396/issue-journal.md; control-plane/aegisops_control_plane/service.py; control-plane/main.py; control-plane/tests/test_cli_inspection.py; control-plane/README.md
- Rollback concern: Low; the new path is read-only and reuses the existing assistant-context/advisory projections instead of introducing new mutable workflow behavior.
- Last focused command: python3 -m unittest control-plane.tests.test_cli_inspection
### Scratchpad
- Reproduced surface gap as argparse invalid choice for `inspect-case-detail`; resolved by adding a reviewed case-detail view that carries linked evidence provenance, reviewed context, and cited advisory output.
