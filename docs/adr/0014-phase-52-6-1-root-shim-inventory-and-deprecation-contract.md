# ADR-0014: Phase 52.6.1 Root Shim Inventory and Deprecation Contract

- **Status**: Accepted
- **Date**: 2026-05-02
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md`
- **Product**: AegisOps
- **Related Issues**: #1105, #1106
- **Depends On**: #1094
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Purpose

Phase 52.6.1 records the root-level compatibility surface under `control-plane/aegisops_control_plane/` before any physical root shim deletion is approved.

This contract is documentation and verification only. It does not delete shims, change imports, rename the public package, change the outer `control-plane/` directory, start Wazuh profile work, start Shuffle profile work, or alter runtime behavior.

## 2. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, adapters, DTOs, projections, summaries, compatibility shims, alias rows, inventory rows, and operator-facing text remain subordinate context.

The root shim inventory does not change authorization, provenance, reconciliation, snapshot, backup, restore, export, readiness, assistant, evidence, action-execution, Wazuh, Shuffle, ticket, CLI, HTTP, or deployment behavior.

## 3. Phase 52.5 Root File Baseline

The Phase 52.5 closeout baseline for root-level Python files under `control-plane/aegisops_control_plane/` is `63`.

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
| `action_lifecycle_write_coordinator.py` | `actions` | simple shim | Candidate for later deletion only after caller evidence, deprecation window, focused import regression, and rollback path are recorded. |
| `action_policy.py` | `actions` | simple shim | Candidate for later deletion only after caller evidence, deprecation window, focused import regression, and rollback path are recorded. |
| `action_receipt_validation.py` | `actions` | simple shim | Candidate for later deletion only after caller evidence, deprecation window, focused import regression, and rollback path are recorded. |
| `action_reconciliation_orchestration.py` | `actions` | simple shim | Candidate for later deletion only after caller evidence, deprecation window, focused import regression, and rollback path are recorded. |
| `action_review_chain.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `action_review_coordination.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `action_review_index.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `action_review_inspection.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `action_review_path_health.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `action_review_projection.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `action_review_timeline.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `action_review_visibility.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `action_review_write_surface.py` | `actions.review` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `ai_trace_lifecycle.py` | `assistant` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `assistant_advisory.py` | `assistant` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `assistant_context.py` | `assistant` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `assistant_provider.py` | `assistant` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `audit_export.py` | `reporting` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `case_workflow.py` | `ingestion` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `cli.py` | `api` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `config.py` | `runtime` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `detection_lifecycle.py` | `ingestion` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `detection_lifecycle_helpers.py` | `ingestion` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `detection_native_context.py` | `ingestion` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `entrypoint_support.py` | `api` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `evidence_linkage.py` | `ingestion` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `execution_coordinator.py` | `actions` | simple shim | Candidate for later deletion only after caller evidence, deprecation window, focused import regression, and rollback path are recorded. |
| `execution_coordinator_action_requests.py` | `actions` | simple shim | Candidate for later deletion only after caller evidence, deprecation window, focused import regression, and rollback path are recorded. |
| `execution_coordinator_delegation.py` | `actions` | simple shim | Candidate for later deletion only after caller evidence, deprecation window, focused import regression, and rollback path are recorded. |
| `execution_coordinator_reconciliation.py` | `actions` | simple shim | Candidate for later deletion only after caller evidence, deprecation window, focused import regression, and rollback path are recorded. |
| `external_evidence_boundary.py` | `evidence` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `external_evidence_endpoint.py` | `evidence` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `external_evidence_facade.py` | `evidence` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `external_evidence_misp.py` | `evidence` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `external_evidence_osquery.py` | `evidence` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `http_protected_surface.py` | `api` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `http_runtime_surface.py` | `api` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `http_surface.py` | `api` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `live_assistant_workflow.py` | `assistant` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `models.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `operations.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `operator_inspection.py` | `reporting` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `persistence_lifecycle.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `phase29_evidently_drift_visibility.py` | `ml_shadow` | compatibility adapter | Retain as a Phase29 legacy adapter; `ml_shadow/drift_visibility.py` is the domain-owned `ml_shadow` implementation. |
| `phase29_mlflow_shadow_model_registry.py` | `ml_shadow` | compatibility adapter | Retain as a Phase29 legacy adapter; `ml_shadow/mlflow_registry.py` is the domain-owned `ml_shadow` implementation. |
| `phase29_shadow_dataset.py` | `ml_shadow` | compatibility adapter | Retain as a Phase29 legacy adapter; `ml_shadow/dataset.py` is the domain-owned `ml_shadow` implementation. |
| `phase29_shadow_scoring.py` | `ml_shadow` | compatibility adapter | Retain as a Phase29 legacy adapter; `ml_shadow/scoring.py` is the domain-owned `ml_shadow` implementation. |
| `pilot_reporting_export.py` | `reporting` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `publishable_paths.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `readiness_contracts.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `readiness_operability.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `record_validation.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `restore_readiness.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `restore_readiness_backup_restore.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `restore_readiness_projection.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `reviewed_slice_policy.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `runtime_boundary.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `runtime_restore_readiness_diagnostics.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `service.py` | `core` | retained compatibility blocker | Retain physically until ADR-0003, ADR-0010, and a later facade transition issue prove the public facade import path can change safely. |
| `service_composition.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |
| `service_snapshots.py` | `runtime` | alias candidate | Candidate for later physical deletion only after caller evidence proves the direct owner import is stable and an alias-preservation test exists. |
| `structured_events.py` | `core` | retained owner | Retain physically until a later owner-move issue proves identical behavior and caller compatibility. |

## 6. Phase29 Boundary

The Phase29 root files are legacy compatibility adapters only. They are not production owners.

The domain-owned implementations are the directly linked `ml_shadow` modules listed in the inventory. Any later removal plan must test both the legacy `phase29_*` import path and the domain-owned `ml_shadow` import path before deleting a root adapter.

## 7. Deprecation Decision Rules

Physical root shim deletion is allowed only when a later issue records the exact root file, replacement owner import path, caller evidence, deprecation window, focused legacy-import regression, rollback path, and authority-boundary impact.

Alias preservation is allowed only when the alias remains a narrow reference to the moved owner and does not make compatibility state, summary text, or module identity authoritative workflow truth.

Retained blockers stay physically present until the referenced compatibility policy is superseded by a later accepted ADR or issue-specific contract.

If a prerequisite signal is missing, malformed, ambiguous, or only partially trusted, the deletion path fails closed and the root file stays available.

## 8. Forbidden Claims

The verifier rejects this contract if it asserts any of these claims outside this section:

- This contract changes runtime behavior.
- This contract allows Phase29 root files as production owners.
- Legacy root shims may be deleted immediately.

## 9. Validation

Run `bash scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh`.

Run `bash scripts/test-verify-phase-52-6-1-root-shim-inventory-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1106 --config <supervisor-config-path>`.

## 10. Non-Goals

- No root-level shim is deleted.
- No import path is changed.
- No public package name is changed.
- No outer repository directory is changed.
- No runtime behavior, HTTP behavior, CLI behavior, deployment behavior, Wazuh behavior, Shuffle behavior, ticket behavior, assistant behavior, evidence behavior, ML behavior, reporting behavior, backup behavior, restore behavior, readiness behavior, or durable-state side effect is changed.
- No Phase29 root file is promoted to production owner.
- No subordinate source becomes authoritative workflow truth.
