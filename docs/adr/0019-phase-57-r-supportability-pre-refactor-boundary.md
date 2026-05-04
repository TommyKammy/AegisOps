# ADR-0019: Phase 57.R Supportability Pre-Refactor Boundary And Inventory

- **Status**: Accepted for Phase 57.R.1 planning and review.
- **Date**: 2026-05-04
- **Related Issues**: #1224, #1225, #1226, #1227, #1228, #1229
- **Depends On**: #1215

## 1. Purpose

Phase 57 accepted the commercial administration MVP before Phase 58 supportability work. Phase 58 is expected to add doctor, backup, restore, upgrade, rollback, and support evidence behavior, so the current admin UI and restore/readiness surfaces need a behavior-preserving refactor boundary before new feature work lands.

This ADR is documentation and verification only. It does not move implementation code, change runtime behavior, change public service facade behavior, change CLI/API behavior, change restore validation semantics, change admin behavior, change RBAC behavior, change persistence, change schema, change approval, change execution, change reconciliation, change AI behavior, or implement Phase 58 supportability features.

## 2. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event truth, limitation, release, gate, restore validation, and closeout truth.

This ADR, extracted helpers, UI posture data, supportability projections, test fixtures, verifier output, issue-lint output, browser state, local cache, admin configuration, role matrix documents, and operator-facing summaries remain subordinate planning, implementation, policy, or validation evidence.

If provenance, scope, auth context, record linkage, snapshot consistency, or restore-validation signals are missing, malformed, ambiguous, or only partially trusted, Phase 57.R work must fail closed and preserve the current guard instead of inferring success.

## 3. Input References

Phase 57.R.1 is governed by these repo-owned references:

- `docs/phase-57-closeout-evaluation.md`
- `docs/maintainability-decomposition-thresholds.md`
- `docs/maintainability-hotspot-baseline.txt`
- `docs/phase-50-maintainability-closeout.md`
- `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md`
- `docs/deployment/support-playbook-break-glass-rehearsal.md`
- `docs/phase-51-4-smb-personas-jobs-to-be-done.md`

The issue also references `Plan&Roadmap/Latest Roadmap.md` for Phase 58 supportability intent. That path is not present in this checkout, so this repo-owned ADR uses the tracked Phase 55-57 closeout handoff text and the tracked persona/gate/supportability docs as the local verification source. If that roadmap file is restored to the repository, Phase 57.R.5 should cross-check this ADR against it before closeout.

## 4. Refactor Inventory

| Class | Current files | Planned extraction owner | Retained behavior |
| --- | --- | --- | --- |
| Phase 57 admin route shell | `apps/operator-ui/src/app/OperatorRoutes.tsx`, `apps/operator-ui/src/app/OperatorShell.tsx`, `apps/operator-ui/src/app/operatorConsolePages/adminPages.tsx` | #1226 | Preserve current admin navigation, role gates, rendered user/role, source profile, action policy, retention, audit export, and AI enablement posture. |
| Phase 57 admin auth posture | `apps/operator-ui/src/auth/roleMatrix.ts`, `apps/operator-ui/src/auth/session.ts`, `apps/operator-ui/src/auth/navigation.ts` | #1226 | Preserve platform admin, analyst, approver, read-only auditor, support operator, and external collaborator restrictions; support and external roles keep workflow authority denied. |
| Phase 57 admin tests | `apps/operator-ui/src/app/OperatorRoutes.authAndShell.testSuite.tsx`, `apps/operator-ui/src/app/OperatorRoutes.test.tsx`, `apps/operator-ui/src/auth/roleMatrix.test.ts`, `apps/operator-ui/src/auth/session.test.ts`, `apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx` | #1226 | Preserve existing admin route, stale-browser-state, optional extension, and role-matrix negative coverage. |
| Restore/readiness runtime | `control-plane/aegisops/control_plane/runtime/restore_readiness.py`, `control-plane/aegisops/control_plane/runtime/restore_readiness_backup_restore.py`, `control-plane/aegisops/control_plane/runtime/restore_readiness_projection.py`, `control-plane/aegisops/control_plane/runtime/runtime_restore_readiness_diagnostics.py`, `control-plane/aegisops/control_plane/runtime/readiness_operability.py`, `control-plane/aegisops/control_plane/runtime/readiness_contracts.py` | #1227 | Preserve backup/restore payload parsing, restore validation, readiness projection, diagnostic shaping, degraded-state reporting, and fail-closed validation semantics. |
| Runtime and facade compatibility | `control-plane/aegisops/control_plane/service.py`, `control-plane/aegisops/control_plane/service_composition.py`, `control-plane/aegisops/control_plane/runtime/runtime_boundary.py`, `control-plane/aegisops/control_plane/api/http_runtime_surface.py`, `control-plane/aegisops/control_plane/api/entrypoint_support.py` | #1227 | Preserve public service facade, HTTP runtime surface, CLI/API behavior, runtime boundary guards, and service composition behavior. |
| Restore/readiness tests | `control-plane/tests/test_service_persistence_restore_readiness.py`, `control-plane/tests/test_phase37_reviewed_record_chain_rehearsal.py`, `control-plane/tests/test_phase57_7_ai_enablement_admin_toggle.py`, `control-plane/tests/test_service_boundary_refactor_regression_validation.py`, `control-plane/tests/test_support_package.py` | #1228 | Preserve rejected restore paths, durable-state cleanliness, authoritative record-chain regression, readiness operability, and support-package import behavior. |
| Maintainability guards | `docs/maintainability-decomposition-thresholds.md`, `docs/maintainability-hotspot-baseline.txt`, `docs/phase-50-maintainability-closeout.md`, `scripts/verify-maintainability-hotspots.sh`, `scripts/test-verify-maintainability-hotspots.sh` | #1229 | Preserve the accepted `service.py` ceiling and treat any new hotspot or silent regrowth as a decomposition decision, not as permission for feature expansion. |

## 5. Extraction Order

| Order | Issue | Scope | Depends on | Verification expectation | Rollback boundary |
| --- | --- | --- | --- | --- | --- |
| 57.R.1 | #1225 Add supportability refactor boundary ADR and inventory | Decision record and inventory only. | #1215 | Run `bash scripts/verify-phase-57-r-supportability-pre-refactor-boundary.sh`, `bash scripts/test-verify-phase-57-r-supportability-pre-refactor-boundary.sh`, `bash scripts/verify-publishable-path-hygiene.sh`, `node <codex-supervisor-root>/dist/index.js issue-lint 1224 --config <supervisor-config-path>`, and `node <codex-supervisor-root>/dist/index.js issue-lint 1225 --config <supervisor-config-path>`. | Revert this ADR and verifier only; no runtime rollback is needed because no runtime files change. |
| 57.R.2 | #1226 Split Phase 57 admin UI pages and posture data | UI and static posture extraction only. | #1225 | Run focused operator UI admin route, auth, session, role-matrix, and optional-extension tests. | Revert the UI module split while keeping the original `adminPages.tsx` rendered behavior and route gates intact. |
| 57.R.3 | #1227 Extract backup / restore payload codec and validation boundaries | Runtime extraction only. | #1225 | Run focused restore/readiness unittest targets and restore drill or authoritative record-chain regression tests that already exist. | Revert the extracted codec and validation modules to the current restore/readiness runtime files without changing public facade or persisted records. |
| 57.R.4 | #1228 Shard restore and readiness tests into focused suites | Test structure only. | #1227 | Run old and new restore/readiness focused test targets and prove rejected paths still leave durable state clean. | Revert test sharding only; do not delete negative coverage or weaken assertions to preserve a split. |
| 57.R.5 | #1229 Phase 57.R closeout evaluation and maintainability guard refresh | Closeout evidence and guard refresh only. | #1226, #1227, #1228 | Run closeout verifier, maintainability hotspot verifier, publishable path hygiene, and issue-lint for #1224 through #1229. | Revert closeout or guard updates if they overclaim supportability completion, hide hotspot regrowth, or conflict with the accepted behavior-preserving evidence. |

## 6. Retained Public Behavior

Phase 57.R work must preserve:

- public service facade behavior and method compatibility;
- CLI/API behavior, HTTP runtime surface behavior, and service composition behavior;
- restore validation semantics, rejected restore behavior, snapshot consistency expectations, and durable-state cleanliness after failed restore paths;
- readiness and operability projection semantics;
- admin UI rendered surfaces, role restrictions, and RBAC posture;
- persistence, schema, migrations, approval, execution, reconciliation, and AI behavior;
- the accepted `service.py` maintainability baseline unless a later ADR explicitly lowers or replaces it.

## 7. Forbidden Claims

The following claims are rejected outside this forbidden-claims section:

- Phase 57.R implements Phase 58 supportability.
- Phase 58 supportability is complete.
- This refactor changes runtime behavior.
- This refactor changes public service facade behavior.
- This refactor changes CLI/API behavior.
- This refactor weakens restore validation.
- This refactor approves admin CRUD expansion.
- This refactor changes RBAC behavior.
- This refactor changes persistence or schema.
- This refactor changes approval, execution, reconciliation, or AI behavior.
- Verifier output is authoritative workflow truth.
- UI cache is authoritative workflow truth.
- Supportability projections are authoritative restore truth.

## 8. Verification

Run:

- `bash scripts/verify-phase-57-r-supportability-pre-refactor-boundary.sh`
- `bash scripts/test-verify-phase-57-r-supportability-pre-refactor-boundary.sh`
- `bash scripts/verify-publishable-path-hygiene.sh`
- `node <codex-supervisor-root>/dist/index.js issue-lint 1224 --config <supervisor-config-path>`
- `node <codex-supervisor-root>/dist/index.js issue-lint 1225 --config <supervisor-config-path>`

## 9. Non-Goals

- Do not move implementation code in Phase 57.R.1.
- Do not implement doctor, backup, restore dry-run, upgrade, rollback, support-bundle, support diagnostics, break-glass support workflow, or customer-support behavior.
- Do not broaden admin CRUD, RBAC, reporting, SOAR, AI, Wazuh, Shuffle, ticketing, approval, execution, reconciliation, persistence, schema, migration, CLI/API, or public facade scope.
- Do not claim Beta, RC, GA, self-service commercial readiness, or commercial replacement readiness.
