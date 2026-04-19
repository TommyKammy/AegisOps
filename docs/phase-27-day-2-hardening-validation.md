# Phase 27 Day-2 Hardening Validation

- Validation status: PASS
- Reviewed on: 2026-04-19
- Scope: confirm the reviewed Phase 27 day-2 hardening drills stay narrow, fail closed, and remain wired into the repo-owned verification path for restore, degraded-mode visibility, identity-boundary failure, and secret-boundary handling.
- Reviewed sources: `docs/runbook.md`, `docs/auth-baseline.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`, `control-plane/tests/test_service_persistence_restore_readiness.py`, `control-plane/tests/test_phase21_runtime_auth_validation.py`, `control-plane/tests/test_runtime_secret_boundary.py`

## Validation Summary

The reviewed restore drill remains specific to the authoritative record chain and continues to prove that restore preserves approval, evidence, action-execution, and reconciliation truth without silently accepting broken runtime bindings.

The degraded-mode validation remains operator-visible instead of permissive. Source-health and delegation outage conditions stay surfaced through readiness diagnostics so operators do not infer healthy ingest or healthy automation from silence.

The identity-boundary validation continues to fail closed for IdP outage and reviewed provider mismatch conditions. Protected surfaces still block when the reviewed identity-provider binding is missing or when an unreviewed provider boundary is presented.

The secret-boundary validation continues to fail closed when the managed backend is unavailable and proves secret rotation is only accepted through a fresh reload of the reviewed OpenBao reference.

## Drill Coverage

- `restore`: `test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain` keeps the approved disaster-recovery path anchored to the authoritative record chain.
- `restore`: `test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore` proves restore verification blocks when the recovered runtime boundary is incomplete.
- `degraded-mode`: `test_service_phase21_readiness_surfaces_source_and_automation_health` keeps source-health and delegation outage visibility explicit during degraded-mode handling.
- `identity-boundary`: `test_startup_status_reports_missing_reviewed_identity_provider_binding` treats IdP outage or missing reviewed provider binding as a fail-closed startup condition.
- `identity-boundary`: `test_protected_surface_request_rejects_unreviewed_identity_provider_boundary` rejects requests that cross the identity boundary through an unreviewed provider path.
- `secret rotation`: `test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load` proves rotation requires a fresh trusted read instead of cached or guessed secret state.
- `secret-backend unavailability`: `test_runtime_config_fails_closed_when_openbao_backend_is_unavailable` keeps the control plane blocked when the reviewed secret backend cannot be read.

These drills stay intentionally narrow. They do not expand into generic chaos engineering, broad performance benchmarking, or new platform-scope reliability experiments.

## Verification

- `bash scripts/verify-phase-27-day-2-hardening-validation.sh`
- `python3 -m unittest control-plane.tests.test_phase27_day2_hardening_validation control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_readiness_surfaces_source_and_automation_health control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_startup_status_reports_missing_reviewed_identity_provider_binding control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_protected_surface_request_rejects_unreviewed_identity_provider_boundary control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_fails_closed_when_openbao_backend_is_unavailable control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load`
- `bash scripts/test-verify-phase-27-day-2-hardening-validation.sh`
- `bash scripts/test-verify-ci-phase-27-workflow-coverage.sh`

## Result

The reviewed Phase 27 day-2 hardening slice now has a repo-owned verification path that covers restore, degraded-mode, identity-boundary, and secret-boundary drills without widening the product thesis or weakening fail-closed behavior.
