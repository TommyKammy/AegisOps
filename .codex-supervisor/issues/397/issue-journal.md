# Issue #397: implementation: add bounded operator actions for case promotion, triage annotations, disposition, and handoff

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/397
- Branch: codex/issue-397
- Workspace: .
- Journal: .codex-supervisor/issues/397/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 880ce696c0c989360b9ee4213ab694a9f23a2421
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-11T22:29:28.416Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 19 was missing bounded service-layer operator actions for durable casework entry after alert promotion; raw `persist_record` existed, but there was no reviewed API or case-detail surface for observations, leads, disposition, and business-hours handoff metadata.
- What changed: Added focused reproducing tests first, then implemented `record_case_observation`, `record_case_lead`, `record_case_recommendation`, `record_case_handoff`, and `record_case_disposition` on the control-plane service. Extended `inspect_case_detail` to return linked observation and lead identifiers/records alongside triage and handoff context merged into the case reviewed context. Tightened the CLI case-detail test to verify the new surface contract.
- Current blocker: none
- Next exact step: Commit this coherent checkpoint, then decide whether a follow-up is needed to expose bounded operator writes through an explicit runtime/API surface beyond the service layer.
- Verification gap: Full `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'` has not been run yet; verified the related service and CLI modules instead.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_cli_inspection.py
- Rollback concern: The implementation stores triage and handoff semantics inside `CaseRecord.reviewed_context`; if later issues formalize first-class fields for those semantics, this slice may need migration or reshaping.
- Last focused command: python3 -m unittest control-plane.tests.test_cli_inspection control-plane.tests.test_service_persistence
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
