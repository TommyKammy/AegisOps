# ADR-0014: Phase 52.6.1 Root Shim Inventory and Deprecation Contract

- **Status**: Accepted
- **Date**: 2026-05-02
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md`
- **Product**: AegisOps
- **Related Issues**: #1105, #1106, #1110
- **Depends On**: #1094
- **Supersedes**: N/A
- **Superseded By**: Phase 52.6.5 retires the Phase29 root filenames listed by this baseline.

---

## 1. Purpose

Phase 52.6.1 records the root-level compatibility surface under `control-plane/aegisops_control_plane/` before broad physical root shim deletion is approved.

This contract is documentation and verification only. Phase 52.6.3 removes only `audit_export.py` as the proof-of-pattern alias-registry candidate; it does not delete broad shim sets, rename the public package, change the outer `control-plane/` directory, start Wazuh profile work, start Shuffle profile work, or alter runtime behavior.

## 2. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, adapters, DTOs, projections, summaries, compatibility shims, alias rows, and operator-facing text remain subordinate context.

The root shim inventory does not change authorization, provenance, reconciliation, snapshot, backup, restore, export, readiness, assistant, evidence, action-execution, Wazuh, Shuffle, ticket, CLI, HTTP, or deployment behavior.

## 3. Phase 52.5 Root File Baseline

The Phase 52.6.5 root-level Python file count under `control-plane/aegisops_control_plane/` is `37` after removing simple physical root shims and the Phase29 root filenames covered by the legacy import alias registry and focused compatibility tests.

The baseline counts only direct `.py` files in `control-plane/aegisops_control_plane/`; package-owned files below subdirectories are tracked by ADR-0012 and stay outside this root shim baseline.

## 4. Classification Rules

Root files are classified with one of these roles:

| Classification | Meaning |
| --- | --- |
| retained owner | A root file still owns live behavior or package identity and is not a deletion candidate in Phase 52.6.1. |
| simple shim | A root file re-exports moved owner symbols and may be deleted only after caller evidence, deprecation window, import regression test, and rollback path exist. |
| compatibility adapter | A root file adapts a legacy API shape to a moved domain owner and must stay until adapter-specific caller evidence and regression tests prove safe removal. |
| alias candidate | A root file currently aliases a moved owner module and may be deleted only after direct-owner imports, alias-preservation expectations, and rollback are documented. |
| retained compatibility blocker | A root file must stay because existing public compatibility policy still requires the root import path. |

If caller evidence is incomplete, malformed, ambiguous, or inferred only from naming, path shape, nearby metadata, comments, or summary text, the root file stays available.

## 5. Root File Inventory

| Root file | Target family | Classification | Deprecation decision |
| --- | --- | --- | --- |
| `__init__.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `action_lifecycle_write_coordinator.py` | `actions` | simple shim | Retain physically because Phase 47 responsibility-decomposition tests and docs still name this root file directly. |
| `action_policy.py` | `actions` | simple shim | Retain physically because Phase 52.5 facade-freeze and canonical-domain-import verifier fixtures still name this root file directly. |
| `action_reconciliation_orchestration.py` | `actions` | simple shim | Retain physically because Phase 49 closeout tests still assert this root file exists. |
| `action_review_projection.py` | `actions.review` | alias candidate | Retain physically because Phase 50 maintainability tests and facade-convergence verifiers still name this root file directly. |
| `action_review_write_surface.py` | `actions.review` | alias candidate | Retain physically because Phase 50 maintainability tests and facade-pressure verifiers still name this root file directly. |
| `ai_trace_lifecycle.py` | `assistant` | alias candidate | Retain physically because Phase 49 and Phase 50 closeout tests still assert this root file exists. |
| `assistant_advisory.py` | `assistant` | alias candidate | Retain physically because Phase 47 responsibility-decomposition tests and docs still name this root file directly. |
| `assistant_context.py` | `assistant` | alias candidate | Retain physically because Phase 50 regression tests still inspect this root file directly; remove only after those tests move to the domain owner path. |
| `case_workflow.py` | `ingestion` | alias candidate | Retain physically because Phase 49 and Phase 50 closeout tests still assert this root file exists. |
| `cli.py` | `api` | alias candidate | Retain physically because service-boundary regression tests still inspect this root file directly. |
| `config.py` | `runtime` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `detection_lifecycle.py` | `ingestion` | alias candidate | Retain physically because Phase 49 closeout tests still assert this root file exists; remove only after that compatibility assertion is superseded. |
| `evidence_linkage.py` | `ingestion` | alias candidate | Retain physically because Phase 49 closeout tests still assert this root file exists. |
| `execution_coordinator_action_requests.py` | `actions` | simple shim | Retain physically because Phase 50 maintainability tests still name this root file directly. |
| `external_evidence_boundary.py` | `evidence` | alias candidate | Retain physically because Phase 47 and Phase 50 tests and verifiers still name this root file directly. |
| `http_protected_surface.py` | `api` | alias candidate | Retain physically because service-boundary regression tests still inspect this root file directly. |
| `http_runtime_surface.py` | `api` | alias candidate | Retain physically because service-boundary regression tests still inspect this root file directly. |
| `http_surface.py` | `api` | alias candidate | Retain physically because service-boundary regression tests still inspect this root file directly. |
| `live_assistant_workflow.py` | `assistant` | alias candidate | Retain physically because Phase 50 regression tests and docs still name this root file directly. |
| `models.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `operator_inspection.py` | `reporting` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `persistence_lifecycle.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `pilot_reporting_export.py` | `reporting` | alias candidate | Retain physically because Phase 49.5 reporting export docs and tests still name this root file directly. |
| `publishable_paths.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `readiness_contracts.py` | `runtime` | alias candidate | Retain physically because Phase 47 responsibility-decomposition tests and docs still name this root file directly. |
| `readiness_operability.py` | `runtime` | alias candidate | Retain physically because service-boundary regression tests still inspect this root file directly; remove only after those tests move to the domain owner path. |
| `record_validation.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `restore_readiness.py` | `runtime` | alias candidate | Retain physically because maintainability docs and Phase 49 closeout tests still name this root file directly. |
| `restore_readiness_backup_restore.py` | `runtime` | alias candidate | Retain physically because restore-readiness persistence tests still inspect this root file directly; remove only after those tests move to the domain owner path. |
| `restore_readiness_projection.py` | `runtime` | alias candidate | Retain physically because restore-readiness persistence tests still inspect this root file directly; remove only after those tests move to the domain owner path. |
| `reviewed_slice_policy.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `runtime_boundary.py` | `runtime` | alias candidate | Retain physically because Phase 49 closeout tests still assert this root file exists. |
| `runtime_restore_readiness_diagnostics.py` | `runtime` | alias candidate | Retain physically because Phase 49 closeout tests still assert this root file exists. |
| `service.py` | `core` | retained compatibility blocker | Retain physically until ADR-0003, ADR-0010, and a later facade transition issue prove the public facade import path can change safely. |
| `service_composition.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `structured_events.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |

## 5.1 Phase 52.6.4 Removed Shim List

Phase 52.6.4 removed these 21 simple physical root shims after adding explicit legacy import alias rows and the focused `control-plane/tests/test_phase52_6_4_root_shim_alias_removal.py` regression:

`action_receipt_validation.py`, `action_review_chain.py`, `action_review_coordination.py`, `action_review_index.py`, `action_review_inspection.py`, `action_review_path_health.py`, `action_review_timeline.py`, `action_review_visibility.py`, `assistant_provider.py`, `detection_lifecycle_helpers.py`, `detection_native_context.py`, `entrypoint_support.py`, `execution_coordinator.py`, `execution_coordinator_delegation.py`, `execution_coordinator_reconciliation.py`, `external_evidence_endpoint.py`, `external_evidence_facade.py`, `external_evidence_misp.py`, `external_evidence_osquery.py`, `operations.py`, and `service_snapshots.py`.

Retained blockers remain physical root files: real root owners (`config.py`, `models.py`, `record_validation.py`, and related core owners), the public `service.py` facade, and root shim files that current regression tests still inspect directly.

## 5.2 Phase 52.6.5 Removed Phase29 Root Filename List

Phase 52.6.5 removed these four Phase29-named root files after adding explicit legacy import alias rows and the focused `control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py` regression:

`phase29_shadow_dataset.py`, `phase29_shadow_scoring.py`, `phase29_evidently_drift_visibility.py`, and `phase29_mlflow_shadow_model_registry.py`.

The production-owned implementations remain under `ml_shadow/dataset.py`, `ml_shadow/scoring.py`, `ml_shadow/drift_visibility.py`, and `ml_shadow/mlflow_registry.py`. The legacy scoring wrapper behavior that differs from canonical scoring now lives in `ml_shadow/legacy_scoring_adapter.py`.

## 5.3 Phase 52.6.6 Retained Root Owner Policy

After Phase 52.6.6, the only retained root owner files are `__init__.py`, `config.py`, `models.py`, `operator_inspection.py`, `persistence_lifecycle.py`, `publishable_paths.py`, `record_validation.py`, `reviewed_slice_policy.py`, `service_composition.py`, and `structured_events.py`.

`service.py` is not a retained owner; it is the single retained compatibility blocker and the public `service.py` facade stays a retained compatibility blocker under ADR-0003 and ADR-0010 until a later facade transition issue supersedes that policy.

No other direct root Python file may be promoted to retained owner status without a later accepted ADR or issue-specific contract that names the root file, authoritative owner, caller evidence, focused regression coverage, rollback path, and authority-boundary impact.

The root package guardrail baseline is exactly `37` direct `.py` files under `control-plane/aegisops_control_plane/`.

No direct root Python filename may begin with `phaseNN` or `phaseNN_` after Phase 52.6.6.

A new flat root module fails verification unless the root file inventory classifies it and the root-count baseline is intentionally updated by policy.

## 6. Phase29 Boundary

The retired Phase29 root filenames were legacy compatibility adapters only. They were not production owners.

The domain-owned implementations are the directly linked `ml_shadow` modules listed in the retired filename list. Legacy `phase29_*` import paths remain available only through the alias registry and focused compatibility tests.

## 7. Deprecation Decision Rules

Physical root shim deletion is allowed only when a later issue records the exact root file, replacement owner import path, caller evidence, deprecation window, focused legacy-import regression, rollback path, and authority-boundary impact.

Alias preservation is allowed only when the alias remains a narrow reference to the moved owner and does not make compatibility state, summary text, or module identity authoritative workflow truth.

Retained blockers stay physically present until the referenced compatibility policy is superseded by a later accepted ADR or issue-specific contract.

If a prerequisite signal is missing, malformed, ambiguous, or only partially trusted, the deletion path fails closed and the root file stays available.

The future public package rename, outer `control-plane/` directory rename, retained-root owner relocation, and `service.py` facade relocation remain blocked until a later accepted ADR names caller evidence, replacement paths, deprecation window, focused regression coverage, rollback path, and authority-boundary impact.

## 8. Forbidden Claims

The verifier rejects this contract if it asserts any of these claims outside this section:

- This contract changes runtime behavior.
- This contract allows Phase29 root files as production owners.
- Legacy root shims may be deleted immediately.

## 9. Validation

Run `bash scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh`.

Run `bash scripts/test-verify-phase-52-6-1-root-shim-inventory-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `bash scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh`.

Run `bash scripts/test-verify-phase-52-6-3-legacy-import-alias-registry.sh`.

Run `bash scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh`.

Run `bash scripts/test-verify-phase-52-6-5-retire-phase29-root-filenames.sh`.

Run `bash scripts/verify-phase-52-6-6-root-package-guardrails.sh`.

Run `bash scripts/test-verify-phase-52-6-6-root-package-guardrails.sh`.

Run `bash scripts/verify-phase-52-5-2-layout-guardrail.sh`.

Run `bash scripts/verify-phase-52-5-9-service-facade-freeze.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1110 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1111 --config <supervisor-config-path>`.

## 10. Non-Goals

- No additional root file beyond the Phase 52.6.4 and Phase 52.6.5 deletion sets is removed by this update.
- No import path is changed.
- No public package name is changed.
- No outer repository directory is changed.
- No runtime behavior, HTTP behavior, CLI behavior, deployment behavior, Wazuh behavior, Shuffle behavior, ticket behavior, assistant behavior, evidence behavior, ML behavior, reporting behavior, backup behavior, restore behavior, readiness behavior, or durable-state side effect is changed.
- No Phase29 root file is promoted to production owner.
- No subordinate source becomes authoritative workflow truth.
