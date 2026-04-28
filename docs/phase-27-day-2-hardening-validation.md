# Phase 27 Day-2 Hardening Validation

- Validation status: PASS
- Reviewed on: 2026-04-20
- Scope: confirm the reviewed Phase 27 day-2 hardening claims are backed by a dedicated repo-owned runtime contract surface, with reused foundational coverage called out explicitly for restore, restore-drill reconciliation truth integrity, degraded-mode visibility, identity-boundary failure, secret delivery, and upgrade/rollback authority-freeze posture.
- Reviewed sources: `docs/runbook.md`, `docs/auth-baseline.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`, `control-plane/tests/test_phase27_day2_runtime_contract.py`, `control-plane/tests/test_service_persistence_restore_readiness.py`, `control-plane/tests/test_phase21_runtime_auth_validation.py`, `control-plane/tests/test_runtime_secret_boundary.py`

## Validation Summary

Phase 27 now has a dedicated runtime-validation surface in `control-plane/tests/test_phase27_day2_runtime_contract.py` instead of relying mainly on narrative aggregation and fixed-line document checks.

That focused module proves the current reviewed path fails closed for post-restore runtime gaps, keeps restored reconciliation mismatch operator-reviewable without auto-closing cases or auto-advancing action state from subordinate receipts, keeps degraded source and automation health operator-visible, rejects missing, unavailable, or unreviewed identity-provider boundaries before operator writes can advance workflow authority, freezes approval, execution, reconciliation, and case lifecycle progression during upgrade or rollback uncertainty, and requires a fresh trusted OpenBao read for secret rotation while blocking interrupted rotation, stale or mixed credential sources, backend outage, plaintext fallback, local file fallback, and protected workflow progression.

The older restore, identity, and secret tests remain part of the evidence set, but they are treated here as foundational coverage reused by Phase 27 rather than being presented as if they were the dedicated Phase 27 contract by themselves.

Upgrade and rollback completion remain reviewed operational contracts and capacity guardrails, but the current runtime now exposes an independent fail-closed authority-freeze check for uncertain, incomplete, or rollback-in-progress control-plane change state. The evidence matrix calls that out explicitly so reviewers do not infer that subordinate receipts, tickets, assistant output, browser state, or optional evidence can advance workflow truth while control-plane state is not verified safe.

## Evidence Matrix

| Phase 27 claim | Dedicated Phase 27 contract coverage | Foundational coverage reused by Phase 27 | Verification command |
| --- | --- | --- | --- |
| Restore runtime guard | `test_phase27_restore_runtime_contract_fails_closed_without_post_restore_bindings` proves a restored control plane does not report success when required runtime bindings are still missing. | `test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain`; `test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore` | `python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract` |
| Restore reconciliation truth integrity | `test_phase27_restore_reconciliation_truth_integrity_keeps_mismatch_reviewable` proves restored subordinate receipts and external-ticket evidence cannot auto-close cases or auto-advance action execution state when the authoritative reconciliation record remains mismatched. | `test_service_fail_closes_when_create_tracking_ticket_reconciliation_receipt_drifts`; `test_service_phase21_restore_rejects_reconciliation_run_binding_mismatch` | `python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract` |
| Degraded-mode visibility | `test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state` proves readiness keeps source and automation degradation visible instead of implying healthy operation from silence. | `test_service_phase21_readiness_surfaces_source_and_automation_health` | `python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract` |
| Identity hardening | `test_phase27_identity_contract_fails_closed_for_missing_or_unreviewed_provider_boundary` proves startup and protected-surface access fail closed when the reviewed IdP binding is absent or crossed through an unreviewed provider. | `test_startup_status_reports_missing_reviewed_identity_provider_binding`; `test_protected_surface_request_rejects_unreviewed_identity_provider_boundary` | `python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract` |
| IdP outage fail-closed workflow authority | `test_phase27_idp_outage_blocks_operator_authority_and_workflow_progression` proves unavailable IdP context blocks protected operator writes before action requests, approval decisions, executions, reconciliations, or case lifecycle transitions can advance. | `test_protected_surface_request_rejects_missing_reviewed_identity_provider_header` | `python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract` |
| Secret delivery and rotation | `test_phase27_secret_contract_requires_fresh_read_and_blocks_backend_outage` proves OpenBao-backed config reloads rotated secrets only through a fresh read and blocks when the backend is unavailable; `test_phase27_secret_backend_outage_rejects_plaintext_fallback_and_blocks_workflow_progression` proves protected-surface secret outage rejects plaintext and file fallback before workflow authority can progress; `test_phase27_secret_rotation_interruption_rejects_mixed_or_partial_credential_state` proves interrupted Wazuh secret rotation rejects mixed direct/OpenBao sources, blocks partial companion-secret reloads, keeps readiness failing closed, and leaves authoritative workflow records unchanged. | `test_runtime_config_fails_closed_when_openbao_backend_is_unavailable`; `test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load` | `python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract` |
| Upgrade/rollback authority freeze | `test_phase27_upgrade_rollback_uncertainty_freezes_authority_sensitive_progression` proves rollback-in-progress control-plane state blocks approval, execution, reconciliation, and case lifecycle progression while readiness remains failing closed and operator-visible. | `docs/runbook.md`; `docs/smb-footprint-and-deployment-profile-baseline.md` | `python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract` |

## Coverage Boundaries

### Phase 27-specific contract coverage

- `control-plane/tests/test_phase27_day2_runtime_contract.py` is the dedicated validation surface for the current reviewed runtime contract.
- `control-plane/tests/test_phase27_day2_hardening_validation.py` verifies the evidence matrix, the coverage split, and the required verification commands remain documented in the repo.

### Foundational coverage reused by Phase 27

- `control-plane/tests/test_service_persistence_restore_readiness.py` remains the deeper restore and readiness evidence pack for record-chain preservation, snapshot consistency, and fail-closed restore checks.
- `control-plane/tests/test_phase21_runtime_auth_validation.py` remains the deeper identity-boundary evidence pack for reviewed reverse-proxy and IdP enforcement.
- `control-plane/tests/test_runtime_secret_boundary.py` remains the deeper managed-secret evidence pack for OpenBao delivery, empty-secret rejection, and file-backed bootstrap paths.

## Verification

- `python3 -m unittest control-plane.tests.test_phase27_day2_hardening_validation control-plane.tests.test_phase27_day2_runtime_contract`
- `python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_readiness_surfaces_source_and_automation_health control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_startup_status_reports_missing_reviewed_identity_provider_binding control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_protected_surface_request_rejects_unreviewed_identity_provider_boundary control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_fails_closed_when_openbao_backend_is_unavailable control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load`
- `bash scripts/verify-phase-27-day-2-hardening-validation.sh`
- `bash scripts/test-verify-phase-27-day-2-hardening-validation.sh`
- `bash scripts/test-verify-ci-phase-27-workflow-coverage.sh`

## Result

The reviewed Phase 27 day-2 hardening slice now shows, from the repository alone, which runtime guarantees are enforced directly by dedicated Phase 27 tests, which older tests are intentionally reused as foundational coverage, and how upgrade or rollback uncertainty freezes authority-sensitive progression until control-plane state is verified safe.
