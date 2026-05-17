# AegisOps Phase 62.6 Automation Simulator Contract

This contract adds a demo/test automation simulator for the reviewed Phase 62 default catalog actions: `enrichment_only_lookup`, `operator_notification`, `manual_escalation_request`, and `create_tracking_ticket`.

## Contract

Every simulator output must be tied to one reviewed catalog action, run only in `demo` or `test` mode, use the reviewed template version for that action, and include explicit `demo_test_label`, `production_exclusion`, and `authority_posture` fields.

Simulator output is demo/test evidence only. It is excluded from production execution receipt and reconciliation truth, and it remains subordinate to AegisOps action request, approval, execution receipt, and reconciliation records.

The simulator must not use live secrets, customer-private data, direct ad-hoc execution, production workflow delegation, production receipts, production reconciliation state, case closure, ticket closure, readiness claims, or any shortcut that treats simulator state as authoritative AegisOps truth.

## Required Output Fields

Each simulator output must include:

- `mode`
- `catalog_action`
- `action_request_id`
- `simulation_run_id`
- `reviewed_template_version`
- `correlation_id`
- `simulated_started_at`
- `simulated_finished_at`
- `simulated_status`
- `demo_test_label`
- `production_exclusion`
- `authority_posture`
- `live_secret_ref`
- `customer_data_classification`
- `simulated_evidence_ref`

Allowed modes are exactly `demo` and `test`. Allowed statuses are `simulated_success`, `simulated_failure`, `simulated_missing_receipt`, `simulated_stale_receipt`, `simulated_mismatched_receipt`, and `simulated_manual_review`.

## Validation Rules

Phase 62.6 validation must fail closed when:

- the catalog action is not one of the reviewed Phase 62 default actions;
- mode is missing or outside `demo` and `test`;
- the simulator output lacks a demo/test evidence label;
- production exclusion is missing;
- authority posture is anything other than `non_authoritative_demo_test_evidence`;
- reviewed template version, catalog action, or required identifiers drift from the reviewed contract;
- live secret use or customer-private data appears;
- simulator output claims production execution receipt truth, reconciliation truth, case truth, ticket truth, closure, readiness, or authority; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented environment variables, or placeholders such as `<supervisor-config-path>` and `<codex-supervisor-root>`.

## Validation

Run `bash scripts/verify-phase-62-6-automation-simulator-contract.sh`.

Run `PYTHONPATH=control-plane:control-plane/tests python3 -m unittest control-plane.tests.test_phase62_action_policy_registry`.

Run `PYTHONPATH=control-plane:control-plane/tests python3 -m unittest control-plane.tests.test_action_receipt_validation`.

Run `bash scripts/verify-phase-54-9-shuffle-authority-boundary-negative-tests.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1320 --config <supervisor-config-path>`.

## Non-Goals

No Controlled Write or Hard Write default enablement, autonomous remediation, destructive response, protected target mutation, approval bypass, execution receipt shortcut, reconciliation shortcut, live Shuffle workflow launch, production receipt creation, production reconciliation state, customer-private data, live secret material, broad SOAR marketplace expansion, Phase 63 evidence expansion, Phase 66 RC proof, Beta readiness, RC readiness, GA readiness, commercial replacement readiness, or broad SOAR replacement readiness is implemented here.
