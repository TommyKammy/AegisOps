# Issue #247: implementation: add a Wazuh alert adapter, fixtures, and signal-admission path

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/247
- Branch: codex/issue-247
- Workspace: .
- Journal: .codex-supervisor/issues/247/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 495abe3795aa0cdbb9e67f3fd0184a625ee914ef
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-06T14:26:16.609Z

## Latest Codex Summary
- Added a concrete `WazuhAlertAdapter`, reviewed Wazuh JSON fixtures, and fixture-backed tests proving Wazuh-origin intake persists first-class analytic signals through `ingest_native_detection_record`.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue #247 was missing a concrete Wazuh-native adapter and fixture-backed proof that native Wazuh alerts flow through the substrate-adapter boundary into first-class `AnalyticSignalRecord` persistence plus linked alert/reconciliation records.
- What changed: Added `control-plane/aegisops_control_plane/adapters/wazuh.py`, exported it from package init files, added two reviewed Wazuh alert fixtures, added focused adapter tests, and added a fixture-backed service persistence test that admits a Wazuh-origin record through `ingest_native_detection_record`.
- Current blocker: none
- Next exact step: Review diff, then push branch or open/update the draft PR if the supervisor wants the checkpoint published.
- Verification gap: Did not run the entire repository test suite; verification is scoped to the new adapter tests, `test_service_persistence`, and the requested `rg` inspection.
- Files touched: control-plane/aegisops_control_plane/__init__.py; control-plane/aegisops_control_plane/adapters/__init__.py; control-plane/aegisops_control_plane/adapters/wazuh.py; control-plane/tests/test_service_persistence.py; control-plane/tests/test_wazuh_adapter.py; control-plane/tests/fixtures/wazuh/agent-origin-alert.json; control-plane/tests/fixtures/wazuh/manager-origin-alert.json
- Rollback concern: Correlation and finding ID derivation are deterministic and currently scoped to reviewed Wazuh fixtures; future broader Wazuh contracts may want different minting semantics without affecting the persistence boundary added here.
- Last focused command: python3 -m unittest control-plane.tests.test_service_persistence
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Focused commands run: `python3 -m unittest control-plane.tests.test_wazuh_adapter`; `python3 -m unittest control-plane.tests.test_service_persistence`; `rg -n "Wazuh|wazuh|AnalyticSignal|NativeDetectionRecordAdapter|fixture" control-plane docs`.
