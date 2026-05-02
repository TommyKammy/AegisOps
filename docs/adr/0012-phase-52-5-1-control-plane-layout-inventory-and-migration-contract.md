# ADR-0012: Phase 52.5.1 Control-Plane Layout Inventory and Migration Contract

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/repository-structure-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #1084, #1085
- **Depends On**: #1073
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Purpose

Phase 52.5.1 recorded the initial `control-plane/aegisops_control_plane/` Python package layout before package moves began, and this accepted contract now tracks the current authoritative owner rows as later Phase 52.5 child issues land.

The inventory assigns every current Python file in the package to a target package family so child issues can move modules deliberately instead of inferring ownership from filename shape or nearby metadata. Rows under package directories are the authoritative owners; flat root rows that say compatibility shim only are temporary legacy import shims.

This contract is documentation and verification only.

## 2. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, adapters, DTOs, projections, summaries, and operator-facing text remain subordinate context.

The layout inventory does not change authorization, provenance, reconciliation, snapshot, backup, restore, export, readiness, assistant, evidence, or action-execution behavior.

## 3. Target Package Families

| Family | Target responsibility |
| --- | --- |
| `core` | Authoritative record model, persistence, lifecycle-neutral service composition, validation, and shared control-plane primitives. |
| `api` | HTTP, protected surface, CLI, and other public process entry surfaces. |
| `runtime` | Startup, configuration, readiness, restore, runtime boundary, operations, and runtime diagnostics. |
| `ingestion` | Detection and alert intake lifecycle modules before records become broader workflow state. |
| `actions` | Action policy, action lifecycle writes, delegation, receipts, reconciliation, and execution coordination. |
| `actions.review` | Reviewed action queue, chain, projection, visibility, inspection, path health, and write surfaces. |
| `evidence` | Evidence linkage, external evidence boundaries, and evidence facade modules. |
| `assistant` | Assistant context, advisory, provider, AI trace, and live assistant workflow modules. |
| `ml_shadow` | Reviewed ML shadow-mode datasets, scoring, registry, and drift visibility modules. |
| `reporting` | Audit export, pilot reporting, and operator inspection surfaces that summarize authoritative state. |
| `adapters` | Substrate adapters for Wazuh, Shuffle, n8n, OpenSearch, PostgreSQL, osquery, MISP, executors, and endpoint evidence. |

## 4. Module Inventory

| Module | Target family | Migration contract |
| --- | --- | --- |
| `__init__.py` | `core` | Keep the public package marker stable while compatibility shims exist. |
| `actions/__init__.py` | `actions` | Package marker for action-owned modules. |
| `actions/action_lifecycle_write_coordinator.py` | `actions` | Owns action lifecycle write behavior while preserving atomic durable write tests. |
| `actions/action_policy.py` | `actions` | Owns reviewed action policy behavior while preserving unchanged fail-closed decisions. |
| `actions/action_receipt_validation.py` | `actions` | Owns receipt validation behavior while preserving rejected-receipt state-cleanliness tests. |
| `actions/action_reconciliation_orchestration.py` | `actions` | Owns direct reconciliation linkage while preserving snapshot-consistent read guarantees. |
| `actions/execution_coordinator.py` | `actions` | Owns execution coordination while preserving authoritative receipt linkage. |
| `actions/execution_coordinator_action_requests.py` | `actions` | Owns action request behavior while preserving fail-closed scope tests. |
| `actions/execution_coordinator_delegation.py` | `actions` | Owns delegation behavior while preserving no substrate-as-authority regression. |
| `actions/execution_coordinator_reconciliation.py` | `actions` | Owns reconciliation behavior while preserving snapshot-consistent read tests. |
| `actions/review/__init__.py` | `actions.review` | Package marker for reviewed-action modules. |
| `actions/review/action_review_chain.py` | `actions.review` | Owns reviewed action chain behavior while preserving legacy import coverage. |
| `actions/review/action_review_coordination.py` | `actions.review` | Owns reviewed action coordination while preserving queue-state regression tests. |
| `actions/review/action_review_index.py` | `actions.review` | Owns reviewed index behavior while preserving authoritative record selection tests. |
| `actions/review/action_review_inspection.py` | `actions.review` | Owns reviewed inspection behavior while preserving direct-link context constraints. |
| `actions/review/action_review_path_health.py` | `actions.review` | Owns reviewed path health behavior while preserving fail-closed missing-signal tests. |
| `actions/review/action_review_projection.py` | `actions.review` | Owns reviewed projection derivation from authoritative records. |
| `actions/review/action_review_timeline.py` | `actions.review` | Owns reviewed timeline derivation while preserving no timeline-as-truth behavior. |
| `actions/review/action_review_visibility.py` | `actions.review` | Owns reviewed visibility behavior while preserving scope-boundary tests. |
| `actions/review/action_review_write_surface.py` | `actions.review` | Owns reviewed write-surface behavior while preserving atomic write tests. |
| `action_lifecycle_write_coordinator.py` | `actions` | Compatibility shim only for the moved action lifecycle write owner. |
| `action_policy.py` | `actions` | Compatibility shim only for the moved reviewed action policy owner. |
| `action_receipt_validation.py` | `actions` | Compatibility shim only for the moved receipt validation owner. |
| `action_reconciliation_orchestration.py` | `actions` | Compatibility shim only for the moved reconciliation orchestration owner. |
| `action_review_chain.py` | `actions.review` | Compatibility shim only for the moved reviewed action chain owner. |
| `action_review_coordination.py` | `actions.review` | Compatibility shim only for the moved reviewed action coordination owner. |
| `action_review_index.py` | `actions.review` | Compatibility shim only for the moved reviewed action index owner. |
| `action_review_inspection.py` | `actions.review` | Compatibility shim only for the moved reviewed action inspection owner. |
| `action_review_path_health.py` | `actions.review` | Compatibility shim only for the moved reviewed action path health owner. |
| `action_review_projection.py` | `actions.review` | Compatibility shim only for the moved reviewed action projection owner. |
| `action_review_timeline.py` | `actions.review` | Compatibility shim only for the moved reviewed action timeline owner. |
| `action_review_visibility.py` | `actions.review` | Compatibility shim only for the moved reviewed action visibility owner. |
| `action_review_write_surface.py` | `actions.review` | Compatibility shim only for the moved reviewed action write-surface owner. |
| `adapters/__init__.py` | `adapters` | Keep adapter package marker stable while adapter imports transition. |
| `adapters/endpoint_evidence.py` | `adapters` | Move only within adapter family while endpoint evidence remains subordinate. |
| `adapters/executor.py` | `adapters` | Move only within adapter family while execution authority remains in control-plane records. |
| `adapters/misp.py` | `adapters` | Move only within adapter family while MISP evidence remains subordinate. |
| `adapters/n8n.py` | `adapters` | Move only within adapter family while n8n remains a routine automation substrate. |
| `adapters/opensearch.py` | `adapters` | Move only within adapter family while OpenSearch remains a substrate, not authority. |
| `adapters/osquery.py` | `adapters` | Move only within adapter family while endpoint evidence remains subordinate. |
| `adapters/postgres.py` | `adapters` | Move only within adapter family with unchanged persistence semantics. |
| `adapters/shuffle.py` | `adapters` | Move only within adapter family while Shuffle remains subordinate execution context. |
| `adapters/wazuh.py` | `adapters` | Move only within adapter family while Wazuh remains subordinate detection context. |
| `api/__init__.py` | `api` | Package marker for API and process entry-surface modules. |
| `api/cli.py` | `api` | Owns CLI entry behavior while preserving command compatibility. |
| `api/entrypoint_support.py` | `api` | Owns entrypoint support behavior while preserving boot semantics. |
| `api/http_protected_surface.py` | `api` | Owns protected HTTP surface behavior while preserving trusted-boundary tests. |
| `api/http_runtime_surface.py` | `api` | Owns runtime HTTP surface behavior while preserving readiness behavior. |
| `api/http_surface.py` | `api` | Owns public HTTP surface behavior while preserving route compatibility tests. |
| `ai_trace_lifecycle.py` | `assistant` | Compatibility shim only for the moved assistant trace lifecycle owner. |
| `assistant/__init__.py` | `assistant` | Package marker for assistant-owned modules. |
| `assistant/ai_trace_lifecycle.py` | `assistant` | Owns assistant trace lifecycle helpers while preserving subordinate-output checks. |
| `assistant/assistant_advisory.py` | `assistant` | Owns advisory coordination while preserving no advisory-as-authority behavior. |
| `assistant/assistant_context.py` | `assistant` | Owns assistant context assembly while preserving direct anchored-context read rules. |
| `assistant/assistant_provider.py` | `assistant` | Owns provider boundary behavior while preserving no placeholder credential acceptance. |
| `assistant/live_assistant_workflow.py` | `assistant` | Owns live assistant workflow behavior while preserving subordinate output checks. |
| `assistant_advisory.py` | `assistant` | Compatibility shim only for the moved assistant advisory owner. |
| `assistant_context.py` | `assistant` | Compatibility shim only for the moved assistant context owner. |
| `assistant_provider.py` | `assistant` | Compatibility shim only for the moved assistant provider owner. |
| `case_workflow.py` | `ingestion` | Compatibility shim only for the moved case workflow owner. |
| `cli.py` | `api` | Compatibility shim only for the moved CLI owner. |
| `config.py` | `runtime` | Move only with runtime config ownership and no sample secret acceptance. |
| `core/__init__.py` | `core` | Package scaffold marker only; no authoritative model, persistence, service, or validation module moves are approved by the marker. |
| `core/legacy_import_aliases.py` | `core` | Owns the bounded legacy import alias registry while preserving explicit owner metadata and no runtime behavior change. |
| `detection_lifecycle.py` | `ingestion` | Compatibility shim only for the moved detection lifecycle owner. |
| `detection_lifecycle_helpers.py` | `ingestion` | Compatibility shim only for the moved detection helper owner. |
| `detection_native_context.py` | `ingestion` | Compatibility shim only for the moved native detection context owner. |
| `entrypoint_support.py` | `api` | Compatibility shim only for the moved entrypoint support owner. |
| `evidence/__init__.py` | `evidence` | Package marker for external-evidence modules. |
| `evidence/external_evidence_boundary.py` | `evidence` | Owns external evidence boundary behavior while preserving subordinate evidence checks. |
| `evidence/external_evidence_endpoint.py` | `evidence` | Owns endpoint evidence helper behavior while preserving unchanged protected-surface behavior. |
| `evidence/external_evidence_facade.py` | `evidence` | Owns evidence facade behavior while preserving legacy import shims. |
| `evidence/external_evidence_misp.py` | `evidence` | Owns MISP evidence behavior while preserving no broadened lineage inference. |
| `evidence/external_evidence_osquery.py` | `evidence` | Owns osquery evidence behavior while preserving no endpoint evidence authority drift. |
| `evidence_linkage.py` | `ingestion` | Compatibility shim only for the moved evidence linkage owner. |
| `execution_coordinator.py` | `actions` | Compatibility shim only for the moved execution coordination owner. |
| `execution_coordinator_action_requests.py` | `actions` | Compatibility shim only for the moved action request owner. |
| `execution_coordinator_delegation.py` | `actions` | Compatibility shim only for the moved delegation owner. |
| `execution_coordinator_reconciliation.py` | `actions` | Compatibility shim only for the moved reconciliation owner. |
| `external_evidence_boundary.py` | `evidence` | Compatibility shim only for the moved external evidence boundary owner. |
| `external_evidence_endpoint.py` | `evidence` | Compatibility shim only for the moved endpoint evidence helper owner. |
| `external_evidence_facade.py` | `evidence` | Compatibility shim only for the moved evidence facade owner. |
| `external_evidence_misp.py` | `evidence` | Compatibility shim only for the moved MISP evidence owner. |
| `external_evidence_osquery.py` | `evidence` | Compatibility shim only for the moved osquery evidence owner. |
| `http_protected_surface.py` | `api` | Compatibility shim only for the moved protected HTTP surface owner. |
| `http_runtime_surface.py` | `api` | Compatibility shim only for the moved runtime HTTP surface owner. |
| `http_surface.py` | `api` | Compatibility shim only for the moved public HTTP surface owner. |
| `ingestion/__init__.py` | `ingestion` | Package marker for ingestion-owned modules. |
| `ingestion/case_workflow.py` | `ingestion` | Owns case workflow behavior while preserving lifecycle state tests. |
| `ingestion/detection_lifecycle.py` | `ingestion` | Owns detection lifecycle behavior while preserving lifecycle transition tests. |
| `ingestion/detection_lifecycle_helpers.py` | `ingestion` | Owns detection helper behavior while preserving authoritative selection rules. |
| `ingestion/detection_native_context.py` | `ingestion` | Owns native detection context behavior while preserving provenance tests. |
| `ingestion/evidence_linkage.py` | `ingestion` | Owns evidence linkage behavior while preserving direct-link constraints. |
| `live_assistant_workflow.py` | `assistant` | Compatibility shim only for the moved live assistant workflow owner. |
| `ml_shadow/__init__.py` | `ml_shadow` | Package marker for reviewed ML shadow-mode modules. |
| `ml_shadow/dataset.py` | `ml_shadow` | Owns shadow dataset lineage while preserving reviewed dataset checks. |
| `ml_shadow/drift_visibility.py` | `ml_shadow` | Owns ML shadow drift visibility while preserving subordinate ML posture. |
| `ml_shadow/legacy_scoring_adapter.py` | `ml_shadow` | Owns legacy scoring import compatibility while canonical scoring remains under `ml_shadow/scoring.py`. |
| `ml_shadow/mlflow_registry.py` | `ml_shadow` | Owns shadow registry behavior while preserving no model-as-authority regression. |
| `ml_shadow/scoring.py` | `ml_shadow` | Owns shadow scoring behavior while preserving subordinate recommendation checks. |
| `models.py` | `core` | Move only with authoritative model import compatibility and schema regression tests. |
| `operations.py` | `runtime` | Compatibility shim only for the moved operations boundary owner. |
| `operator_inspection.py` | `reporting` | Move only with operator inspection derivation tests from authoritative records. |
| `persistence_lifecycle.py` | `core` | Move only with persistence lifecycle ownership and all-or-nothing mutation tests. |
| `phase29_evidently_drift_visibility.py` | `ml_shadow` | Compatibility shim only for the moved ML shadow drift visibility owner. |
| `phase29_mlflow_shadow_model_registry.py` | `ml_shadow` | Compatibility shim only for the moved shadow registry owner. |
| `phase29_shadow_dataset.py` | `ml_shadow` | Compatibility shim only for the moved shadow dataset owner. |
| `phase29_shadow_scoring.py` | `ml_shadow` | Compatibility shim only for the moved shadow scoring owner. |
| `pilot_reporting_export.py` | `reporting` | Compatibility shim only for the moved pilot reporting export owner. |
| `publishable_paths.py` | `core` | Move only with publishable path hygiene ownership and workstation-local path tests. |
| `readiness_contracts.py` | `runtime` | Compatibility shim only for the moved readiness contract owner. |
| `readiness_operability.py` | `runtime` | Compatibility shim only for the moved readiness operability owner. |
| `record_validation.py` | `core` | Move only with authoritative record validation ownership and malformed input tests. |
| `reporting/__init__.py` | `reporting` | Package marker for reporting-owned modules. |
| `reporting/audit_export.py` | `reporting` | Owns audit export behavior while preserving snapshot consistency and no partial durable write on failure. |
| `reporting/pilot_reporting_export.py` | `reporting` | Owns pilot reporting export behavior while preserving snapshot-consistent export tests. |
| `restore_readiness.py` | `runtime` | Compatibility shim only for the moved restore readiness owner. |
| `restore_readiness_backup_restore.py` | `runtime` | Compatibility shim only for the moved backup/restore owner. |
| `restore_readiness_projection.py` | `runtime` | Compatibility shim only for the moved restore projection owner. |
| `reviewed_slice_policy.py` | `core` | Move only with reviewed-slice policy ownership and direct scope binding tests. |
| `runtime/__init__.py` | `runtime` | Package marker for runtime-owned modules. |
| `runtime/operations.py` | `runtime` | Owns operations boundary behavior while preserving operator command behavior. |
| `runtime/readiness_contracts.py` | `runtime` | Owns readiness contract behavior while preserving fail-closed readiness checks. |
| `runtime/readiness_operability.py` | `runtime` | Owns readiness operability behavior while preserving no status-as-truth drift. |
| `runtime/restore_readiness.py` | `runtime` | Owns restore readiness behavior while preserving clean failed-restore state tests. |
| `runtime/restore_readiness_backup_restore.py` | `runtime` | Owns backup/restore behavior while preserving all-or-nothing restore tests. |
| `runtime/restore_readiness_projection.py` | `runtime` | Owns restore projection derivation from authoritative state. |
| `runtime/runtime_boundary.py` | `runtime` | Owns runtime trust boundary behavior while preserving untrusted-header tests. |
| `runtime/runtime_restore_readiness_diagnostics.py` | `runtime` | Owns diagnostics behavior while preserving no mixed-snapshot aggregation. |
| `runtime/service_snapshots.py` | `runtime` | Owns runtime snapshot behavior while preserving snapshot-consistent read tests. |
| `runtime_boundary.py` | `runtime` | Compatibility shim only for the moved runtime trust boundary owner. |
| `runtime_restore_readiness_diagnostics.py` | `runtime` | Compatibility shim only for the moved diagnostics owner. |
| `service.py` | `core` | Keep the public facade import path stable until facade compatibility policy is superseded. |
| `service_composition.py` | `core` | Move only with service composition ownership and unchanged facade construction. |
| `service_snapshots.py` | `runtime` | Compatibility shim only for the moved runtime snapshot owner. |
| `structured_events.py` | `core` | Move only with structured event ownership and unchanged event payload semantics. |

## 5. Compatibility Shim Expectations

The public Python package name `aegisops_control_plane` remains unchanged throughout Phase 52.5.1 and later child issues unless a later accepted ADR explicitly approves a rename.

The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.

Legacy import paths remain available during migration through compatibility shims, direct re-export modules, or approved entries in the legacy import alias registry until all documented internal, CLI, HTTP, test, and operator callers have migrated.

The Phase 52.6.3 registry is owned by `control-plane/aegisops_control_plane/core/legacy_import_aliases.py`, preserves explicit owner metadata for each approved alias row, and replaces the removed `control-plane/aegisops_control_plane/audit_export.py` root shim for `aegisops_control_plane.audit_export`.

Removing a legacy import path requires a later transition policy that lists the affected import path, replacement import path, caller evidence, deprecation window, focused regression test, and rollback path.

Compatibility shims must be narrow: they may re-export or delegate to the new owner, but they must not make Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, projections, summaries, or adapter state authoritative.

If caller evidence is incomplete, malformed, or ambiguous, the old import path stays available.

## 6. Deferred Renames

The public package rename is deferred because external and internal callers currently import `aegisops_control_plane`, and renaming it before compatibility evidence would create avoidable runtime and test breakage.

The outer directory rename is deferred because `control-plane/` is already the approved repository-structure baseline for live control-plane code and must stay distinct from `postgres/control-plane/` persistence-contract assets.

Phase 52.5.1 does not itself approve any additional production module moves, import rewrites beyond the documented compatibility shims, package renames, directory renames, Wazuh profile work, Shuffle profile work, runtime behavior changes, deployment behavior changes, or authority-boundary changes.

## 7. Forbidden Claims

The verifier rejects this contract if it asserts any of these claims outside this section:

- This contract changes runtime behavior.
- This contract implements Wazuh product profiles.
- This contract implements Shuffle product profiles.
- Legacy imports may be removed immediately.

## 8. Validation

Run `bash scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`.

Run `bash scripts/test-verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1085 --config <supervisor-config-path>`.

## 9. Non-Goals

- No production module is moved except the authoritative owner rows documented in this inventory by later Phase 52.5 child issues.
- No production import path is changed except the documented compatibility shims that preserve legacy imports while callers migrate.
- No public package name is changed.
- No outer repository directory is changed.
- No runtime behavior, HTTP behavior, CLI behavior, deployment behavior, Wazuh behavior, Shuffle behavior, ticket behavior, assistant behavior, evidence behavior, ML behavior, reporting behavior, backup behavior, restore behavior, readiness behavior, or durable-state side effect is changed.
- No subordinate source becomes authoritative workflow truth.
