# Phase 50.10.5 Facade Method Rewiring

Phase 50.10.5 is a behavior-preserving maintainability slice for issue #992. It reduces `AegisOpsControlPlaneService` facade pressure by rewiring internal lifecycle-transition callers to the focused detection lifecycle collaborator.

## Rewired Callers

- `control-plane/aegisops_control_plane/service_composition.py` now passes restore/readiness lifecycle synthesis through `DetectionIntakeService.lifecycle_transition_helper.build_lifecycle_transition_record`.
- `control-plane/aegisops_control_plane/external_evidence_endpoint.py` now builds endpoint action-request lifecycle transitions through `DetectionIntakeService.lifecycle_transition_helper.build_lifecycle_transition_records`.

The removed facade delegates were private lifecycle-transition compatibility methods:

- `_build_lifecycle_transition_record`
- `_build_lifecycle_transition_records`

HTTP, CLI, and documented public service entrypoints remain unchanged.

## Accepted Residual Facade Ceiling

After this rewiring, the maintainability verifier reports the remaining accepted service hotspot as:

- `lines=3003`
- `effective_lines=2704`
- `max_facade_methods=167`
- `facade_class=AegisOpsControlPlaneService`
- `adr_exception=ADR-0003`
- `phase=50.10.5`
- `issue=#992`

The facade remains above the long-term 1,500-line and 50-method targets, so the baseline is still an exception and not a general growth allowance.

## Verification

Run:

- `python3 -m unittest control-plane/tests/test_service_boundary_refactor_regression_validation.py control-plane/tests/test_service_persistence_ingest_case_lifecycle.py`
- `bash scripts/verify-maintainability-hotspots.sh`
