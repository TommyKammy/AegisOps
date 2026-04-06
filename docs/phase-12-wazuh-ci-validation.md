# Phase 12 Wazuh Ingest and Workflow CI Validation

- Validation date: 2026-04-07
- Validation scope: Phase 12 review of Wazuh ingest contract coverage, fixture-backed admissions, alert and case lifecycle behavior, analyst queue invariants, and CI wiring for the reviewed Wazuh control-plane path
- Baseline references: `docs/wazuh-alert-ingest-contract.md`, `docs/wazuh-rule-lifecycle-runbook.md`, `control-plane/tests/test_wazuh_alert_ingest_contract_docs.py`, `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_cli_inspection.py`, `.github/workflows/ci.yml`
- Verification commands: `bash scripts/verify-wazuh-rule-lifecycle-runbook.sh`, `python3 -m unittest control-plane.tests.test_wazuh_alert_ingest_contract_docs control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection`, `bash scripts/test-verify-ci-phase-12-workflow-coverage.sh`, `bash scripts/verify-phase-12-wazuh-ci-validation.sh`
- Validation status: PASS

## Required Boundary Artifacts

- `docs/wazuh-alert-ingest-contract.md`
- `docs/wazuh-rule-lifecycle-runbook.md`
- `control-plane/tests/test_wazuh_alert_ingest_contract_docs.py`
- `control-plane/tests/test_wazuh_adapter.py`
- `control-plane/tests/test_service_persistence.py`
- `control-plane/tests/test_cli_inspection.py`
- `.github/workflows/ci.yml`

## Review Outcome

Confirmed the reviewed Wazuh ingest contract remains explicit about native identifier preservation, namespaced `substrate_detection_record_id` linkage, native timing preservation, and accountable source provenance.

Confirmed fixture-backed Wazuh adapter coverage still admits both agent-origin and manager-origin alerts through the reviewed substrate-adapter boundary.

Confirmed the reviewed service persistence path still admits Wazuh-origin analytic signals, preserves restated case linkage, and exposes analyst queue records with Wazuh-native rule and accountable source context.

Confirmed analyst queue review keeps Wazuh-specific source precedence when multi-source linkage is present so queue routing does not drift away from the reviewed Phase 12 ingest path.

Confirmed the CLI inspection path still renders the read-only Wazuh business-hours analyst queue view from the same reviewed control-plane state.

Confirmed CI now runs a dedicated Phase 12 validation step and a workflow coverage guard so failures point to the reviewed Wazuh ingest and workflow boundary instead of only surfacing through broad suite discovery.

## Cross-Link Review

`docs/wazuh-alert-ingest-contract.md` must continue to define the reviewed Wazuh-native required fields, provenance set, and identifier mapping that the Phase 12 intake path preserves.

`docs/wazuh-rule-lifecycle-runbook.md` must continue to require fixture refresh and aligned adapter and persistence tests before downstream workflow logic relies on a Wazuh rule change.

`control-plane/tests/test_wazuh_alert_ingest_contract_docs.py` must continue to guard the reviewed Wazuh contract document and its required cross-links.

`control-plane/tests/test_wazuh_adapter.py` must continue to guard fixture-backed Wazuh native-record and source-identity admission behavior.

`control-plane/tests/test_service_persistence.py` must continue to guard Wazuh ingest admission, alert and case lifecycle linkage, and analyst queue invariants.

`control-plane/tests/test_cli_inspection.py` must continue to guard the read-only Wazuh analyst queue inspection path.

`.github/workflows/ci.yml` must continue to run the dedicated Phase 12 validation step, the focused Wazuh unit-test command, and the workflow coverage guard.

## Deviations

No deviations found.
