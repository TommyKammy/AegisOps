# Issue #408: implementation: constrain the Phase 19 operator workflow to the approved Wazuh-backed GitHub audit slice

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/408
- Branch: codex/issue-408
- Workspace: .
- Journal: .codex-supervisor/issues/408/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 4f8e280ffb144da4ba71ae19fe19bc24e6148282
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-12T10:08:44.608Z

## Latest Codex Summary
- Reproduced the gap with focused Phase 19 service tests: replay-only GitHub audit cases and broader-family Wazuh-backed cases still allowed `inspect_case_detail` and bounded casework writes.
- Added a fail-closed Phase 19 eligibility gate in the service layer so case detail and bounded write actions only admit cases linked to live `live_wazuh_webhook` provenance, Wazuh-backed reconciliation, and `github_audit` source family.
- Updated service and CLI tests to seed approved in-scope casework from the reviewed live Wazuh GitHub audit fixture, and added focused negative coverage for rejected replay-only and broader-family cases.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 19 case detail and bounded casework paths were only checking that a case existed, so replay-only or broader-family cases could enter the operator surface even though live intake was already narrowed to the reviewed Wazuh GitHub audit slice.
- What changed: Added `_require_phase19_operator_case` and slice eligibility helpers in `control-plane/aegisops_control_plane/service.py`; gated `inspect_case_detail`, `record_case_observation`, `record_case_lead`, `record_case_recommendation`, `record_case_handoff`, and `record_case_disposition`; added focused rejection tests in `control-plane/tests/test_service_persistence.py`; updated CLI/runtime casework tests in `control-plane/tests/test_cli_inspection.py` to use the approved live Wazuh GitHub audit path.
- Current blocker: none
- Next exact step: Commit the service/test changes on `codex/issue-408`.
- Verification gap: none after local full-suite discovery
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_cli_inspection.py`
- Rollback concern: Reverting the eligibility gate would silently reopen replay-only and broader-family cases to the Phase 19 operator workflow.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
