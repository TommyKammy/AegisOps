# Issue #260: implementation: add reviewed case-promotion behavior for Wazuh-driven alerts

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/260
- Branch: codex/issue-260
- Workspace: .
- Journal: .codex-supervisor/issues/260/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: 4b910a490e847be880d039e7ef87cad3c18b5ecf
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-06T22:44:13.000Z

## Latest Codex Summary
Implemented the reviewed Wazuh case-promotion path in [service.py](control-plane/aegisops_control_plane/service.py). `AegisOpsControlPlaneService.promote_alert_to_case(...)` now creates or updates durable `CaseRecord` state from the alert review path, escalates the alert to `escalated_to_case`, links the analytic signal, backfills linked evidence onto the case, and updates reconciliation linkage so later Wazuh restatements keep the promoted `case_id`.

I tightened the reproducer in [test_service_persistence.py](control-plane/tests/test_service_persistence.py) and [test_cli_inspection.py](control-plane/tests/test_cli_inspection.py) so they no longer rely on manually preseeded case rows, and aligned the reviewed semantics in [control-plane-state-model.md](docs/control-plane-state-model.md) and [wazuh-alert-ingest-contract.md](docs/wazuh-alert-ingest-contract.md). Checkpoint commit: `4b910a4` (`Add reviewed Wazuh case promotion path`).

Tests run: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection control-plane.tests.test_wazuh_alert_ingest_contract_docs` and `rg -n "case-promotion|CaseRecord|escalated_to_case|case_id|Wazuh" control-plane docs`.

Summary: Added a service-owned reviewed case-promotion path for Wazuh alerts, reran focused verification, pushed `codex/issue-260`, and opened draft PR #263.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection`; `python3 -m unittest control-plane.tests.test_wazuh_alert_ingest_contract_docs`
Next action: Monitor draft PR #263 for review or CI feedback and address any follow-up fixes on `codex/issue-260`
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The missing behavior was a service-owned reviewed promotion path; ingest could preserve an existing `case_id`, but nothing created or updated the durable `CaseRecord` and linked evidence/reconciliation state from Wazuh-driven alert handling.
- What changed: Added `AegisOpsControlPlaneService.promote_alert_to_case`, updated Wazuh persistence and CLI tests to use the service promotion path instead of manual preseeded case rows, and documented reviewed Wazuh case-promotion semantics in the control-plane state model and Wazuh ingest contract.
- Current blocker: none
- Next exact step: Monitor draft PR #263 and respond to any review or CI findings without broadening scope beyond the reviewed Wazuh case-promotion path.
- Verification gap: Did not run the full repository test suite outside the targeted control-plane and Wazuh contract checks; only the focused issue command set was rerun during stabilization.
- Published state: Branch `codex/issue-260` pushed to origin and draft PR `#263` opened against `main`.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_cli_inspection.py; docs/control-plane-state-model.md; docs/wazuh-alert-ingest-contract.md; .codex-supervisor/issues/260/issue-journal.md
- Rollback concern: The new promotion path updates evidence and reconciliation linkage for every reconciliation record tied to the promoted alert; if later review wants narrower historical mutation semantics, revisit `_link_case_to_alert_reconciliations`.
- Last focused command: python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection control-plane.tests.test_wazuh_alert_ingest_contract_docs
- Additional verification command: rg -n "case-promotion|CaseRecord|escalated_to_case|case_id|Wazuh" control-plane docs
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
