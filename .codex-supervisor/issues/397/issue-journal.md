# Issue #397: implementation: add bounded operator actions for case promotion, triage annotations, disposition, and handoff

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/397
- Branch: codex/issue-397
- Workspace: .
- Journal: .codex-supervisor/issues/397/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: dc9e027a779274703198b9af8bdb98872b9ebc2d
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-11T22:38:53.361Z

## Latest Codex Summary
Implemented a bounded Phase 19 casework slice in the control-plane service and checkpointed it in `dc9e027` (`Add bounded operator casework actions`).

The service now has explicit bounded operator actions for `record_case_observation`, `record_case_lead`, `record_case_recommendation`, `record_case_handoff`, and `record_case_disposition`, instead of relying on raw `persist_record`. `inspect_case_detail` now surfaces linked observations and leads, and the case reviewed context now carries reviewed triage and business-hours handoff metadata. I added a focused reproducer first, then tightened the CLI case-detail coverage so the reviewed surface proves the new artifacts show up.

Verification ran clean on the related slice:
`python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_records_bounded_casework_actions_for_triage_disposition_and_handoff`
`python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_records_bounded_casework_actions_for_triage_disposition_and_handoff control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_cli_renders_case_detail_with_evidence_provenance_and_cited_advisory_output`
`python3 -m unittest control-plane.tests.test_cli_inspection control-plane.tests.test_service_persistence`

Summary: Added bounded operator casework actions and exposed their outputs on the reviewed case-detail surface; committed as `dc9e027`.
State hint: implementing
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_records_bounded_casework_actions_for_triage_disposition_and_handoff`; `python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_records_bounded_casework_actions_for_triage_disposition_and_handoff control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_cli_renders_case_detail_with_evidence_provenance_and_cited_advisory_output`; `python3 -m unittest control-plane.tests.test_cli_inspection control-plane.tests.test_service_persistence`
Next action: Decide whether to expose these bounded casework writes through an explicit runtime/API surface beyond the service layer, then run the full `control-plane/tests` discovery sweep if needed.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining Phase 19 gap was not in the service layer anymore; it was the reviewed operator surface itself. Operators could inspect alert and case detail, but could not yet promote alerts or record bounded casework actions through the CLI/runtime surface.
- What changed: Added explicit bounded operator commands and HTTP endpoints in `control-plane/main.py` for `promote-alert-to-case`, `record-case-observation`, `record-case-lead`, `record-case-recommendation`, `record-case-handoff`, and `record-case-disposition`. The runtime now accepts JSON POSTs for the same bounded actions under `/operator/*`, with strict string/list/datetime validation before delegating into the already-bounded service methods. Added focused CLI and HTTP tests that exercise the full promote-to-casework flow and verify the resulting reviewed case-detail state.
- Current blocker: none
- Next exact step: Commit this coherent checkpoint, push `codex/issue-397`, and open a draft PR if one still does not exist.
- Verification gap: none for the implemented slice; the focused operator-surface tests passed and the full `control-plane/tests` discovery sweep passed.
- Files touched: control-plane/main.py; control-plane/tests/test_cli_inspection.py
- Rollback concern: The new write surface intentionally mirrors current service semantics, so any future schema change to case triage or handoff metadata will require corresponding CLI/HTTP payload reshaping.
- Last focused command: python3 -m unittest discover -s control-plane/tests -p 'test_*.py'
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
