# Phase 11 Control-Plane Persistence and Vendor-Neutral CI Validation

- Validation date: 2026-04-06
- Validation scope: Phase 11 review of PostgreSQL-authoritative control-plane persistence, vendor-neutral analytic-signal and execution-surface coverage, and CI wiring for the reviewed local runtime and inspection paths
- Baseline references: `docs/control-plane-state-model.md`, `control-plane/README.md`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_postgres_store.py`, `control-plane/tests/test_cli_inspection.py`, `.github/workflows/ci.yml`
- Verification commands: `bash scripts/verify-control-plane-state-model-doc.sh`, `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_postgres_store control-plane.tests.test_cli_inspection`, `bash scripts/test-verify-ci-phase-11-workflow-coverage.sh`, `bash scripts/verify-phase-11-control-plane-ci-validation.sh`
- Validation status: PASS

## Required Boundary Artifacts

- `docs/control-plane-state-model.md`
- `control-plane/README.md`
- `control-plane/tests/test_service_persistence.py`
- `control-plane/tests/test_postgres_store.py`
- `control-plane/tests/test_cli_inspection.py`
- `.github/workflows/ci.yml`

## Review Outcome

Confirmed the reviewed runtime and inspection paths report `persistence_mode="postgresql"` and treat the PostgreSQL-backed control-plane store as the authoritative local persistence path.

Confirmed analytic signals remain first-class control-plane records with durable `analytic_signal_id` and `substrate_detection_record_id` linkage instead of collapsing into alert-only state.

Confirmed native detection intake remains constrained by explicit substrate-adapter boundaries and non-empty substrate-origin identifiers.

Confirmed reconciliation coverage preserves vendor-neutral `execution_surface_type`, `execution_surface_id`, and `execution_run_id` assumptions so the reviewed tests do not hard-code one automation substrate implementation.

Confirmed CI now runs a dedicated Phase 11 validation step and a workflow coverage guard so failures point to this reviewed boundary instead of only surfacing through broad unit-test discovery.

## Cross-Link Review

`docs/control-plane-state-model.md` must continue to describe the reviewed local runtime as `persistence_mode="postgresql"` and the PostgreSQL-backed control-plane store as the authoritative local persistence path.

`control-plane/README.md` must continue to describe the reviewed runtime and inspection commands as the authoritative local operator flow while keeping injected in-memory stores limited to tests and local doubles.

`control-plane/tests/test_postgres_store.py` must continue to guard authoritative PostgreSQL persistence mode reporting.

`control-plane/tests/test_service_persistence.py` must continue to guard substrate-adapter intake boundaries, first-class analytic-signal handling, and vendor-neutral execution-surface reconciliation.

`control-plane/tests/test_cli_inspection.py` must continue to guard the reviewed runtime and inspection paths against PostgreSQL-backed read-only control-plane views.

`.github/workflows/ci.yml` must continue to run the dedicated Phase 11 validation step, the focused Phase 11 unit-test command, and the workflow coverage guard.

## Deviations

No deviations found.
