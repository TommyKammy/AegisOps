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

Phase 52.5.1 records the current `control-plane/aegisops_control_plane/` Python package layout before any package moves happen.

The inventory assigns every current Python file in the package to a target package family so later child issues can move modules deliberately instead of inferring ownership from filename shape or nearby metadata.

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
| `actions/__init__.py` | `actions` | Package scaffold marker only; no action lifecycle module moves are approved by the marker. |
| `actions/review/__init__.py` | `actions.review` | Package scaffold marker only; no reviewed-action module moves are approved by the marker. |
| `action_lifecycle_write_coordinator.py` | `actions` | Move only with action lifecycle write ownership and atomic durable write tests. |
| `action_policy.py` | `actions` | Move only with reviewed action policy caller evidence and unchanged fail-closed decisions. |
| `action_receipt_validation.py` | `actions` | Move only with receipt validation ownership and rejected-receipt state-cleanliness tests. |
| `action_reconciliation_orchestration.py` | `actions` | Move only with direct reconciliation linkage and snapshot-consistent read guarantees. |
| `action_review_chain.py` | `actions.review` | Move only with reviewed action chain authority and legacy import coverage. |
| `action_review_coordination.py` | `actions.review` | Move only with reviewed action coordination ownership and queue-state regression tests. |
| `action_review_index.py` | `actions.review` | Move only with reviewed index ownership and authoritative record selection tests. |
| `action_review_inspection.py` | `actions.review` | Move only with reviewed inspection ownership and direct-link context constraints. |
| `action_review_path_health.py` | `actions.review` | Move only with reviewed path health ownership and fail-closed missing-signal tests. |
| `action_review_projection.py` | `actions.review` | Move only with reviewed projection derivation tests from authoritative records. |
| `action_review_timeline.py` | `actions.review` | Move only with reviewed timeline derivation and no timeline-as-truth regression tests. |
| `action_review_visibility.py` | `actions.review` | Move only with reviewed visibility ownership and scope-boundary tests. |
| `action_review_write_surface.py` | `actions.review` | Move only with reviewed write-surface ownership and atomic write tests. |
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
| `api/__init__.py` | `api` | Package scaffold marker only; no HTTP, CLI, endpoint, or protected-surface module moves are approved by the marker. |
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
| `audit_export.py` | `reporting` | Compatibility shim only for the moved audit export owner. |
| `case_workflow.py` | `core` | Move only with authoritative case workflow ownership and lifecycle state tests. |
| `cli.py` | `api` | Move only after CLI import compatibility and command behavior are preserved. |
| `config.py` | `runtime` | Move only with runtime config ownership and no sample secret acceptance. |
| `core/__init__.py` | `core` | Package scaffold marker only; no authoritative model, persistence, service, or validation module moves are approved by the marker. |
| `detection_lifecycle.py` | `ingestion` | Move only with detection lifecycle authority and lifecycle transition tests. |
| `detection_lifecycle_helpers.py` | `ingestion` | Move only with detection helper ownership and unchanged authoritative selection rules. |
| `detection_native_context.py` | `ingestion` | Move only with native detection context ownership and provenance tests. |
| `entrypoint_support.py` | `runtime` | Move only with startup entrypoint ownership and unchanged boot semantics. |
| `evidence/__init__.py` | `evidence` | Package scaffold marker only; no evidence boundary or facade module moves are approved by the marker. |
| `evidence_linkage.py` | `evidence` | Move only with evidence linkage ownership and direct-link constraints. |
| `execution_coordinator.py` | `actions` | Move only with execution coordination ownership and authoritative receipt linkage. |
| `execution_coordinator_action_requests.py` | `actions` | Move only with action request ownership and fail-closed scope tests. |
| `execution_coordinator_delegation.py` | `actions` | Move only with delegation ownership and no substrate-as-authority regression. |
| `execution_coordinator_reconciliation.py` | `actions` | Move only with reconciliation ownership and snapshot-consistent read tests. |
| `external_evidence_boundary.py` | `evidence` | Move only with external evidence boundary ownership and subordinate evidence checks. |
| `external_evidence_endpoint.py` | `api` | Move only with endpoint routing ownership and unchanged protected-surface behavior. |
| `external_evidence_facade.py` | `evidence` | Move only with evidence facade compatibility and legacy import shims. |
| `external_evidence_misp.py` | `evidence` | Move only with MISP evidence ownership and no broadened lineage inference. |
| `external_evidence_osquery.py` | `evidence` | Move only with osquery evidence ownership and no endpoint evidence authority drift. |
| `http_protected_surface.py` | `api` | Move only with protected HTTP surface ownership and trusted-boundary tests. |
| `http_runtime_surface.py` | `api` | Move only with runtime HTTP surface ownership and unchanged readiness behavior. |
| `http_surface.py` | `api` | Move only with public HTTP surface ownership and route compatibility tests. |
| `ingestion/__init__.py` | `ingestion` | Package scaffold marker only; no detection intake module moves are approved by the marker. |
| `live_assistant_workflow.py` | `assistant` | Compatibility shim only for the moved live assistant workflow owner. |
| `ml_shadow/__init__.py` | `ml_shadow` | Package scaffold marker only; no ML shadow-mode module moves are approved by the marker. |
| `models.py` | `core` | Move only with authoritative model import compatibility and schema regression tests. |
| `operations.py` | `runtime` | Move only with operations boundary ownership and unchanged operator command behavior. |
| `operator_inspection.py` | `reporting` | Move only with operator inspection derivation tests from authoritative records. |
| `persistence_lifecycle.py` | `core` | Move only with persistence lifecycle ownership and all-or-nothing mutation tests. |
| `phase29_evidently_drift_visibility.py` | `ml_shadow` | Move only with ML shadow drift visibility ownership and subordinate ML posture. |
| `phase29_mlflow_shadow_model_registry.py` | `ml_shadow` | Move only with shadow registry ownership and no model-as-authority regression. |
| `phase29_shadow_dataset.py` | `ml_shadow` | Move only with shadow dataset ownership and reviewed dataset lineage checks. |
| `phase29_shadow_scoring.py` | `ml_shadow` | Move only with shadow scoring ownership and subordinate recommendation checks. |
| `pilot_reporting_export.py` | `reporting` | Compatibility shim only for the moved pilot reporting export owner. |
| `publishable_paths.py` | `core` | Move only with publishable path hygiene ownership and workstation-local path tests. |
| `readiness_contracts.py` | `runtime` | Move only with readiness contract ownership and unchanged fail-closed readiness checks. |
| `readiness_operability.py` | `runtime` | Move only with readiness operability ownership and no status-as-truth drift. |
| `record_validation.py` | `core` | Move only with authoritative record validation ownership and malformed input tests. |
| `reporting/__init__.py` | `reporting` | Package marker for reporting-owned modules. |
| `reporting/audit_export.py` | `reporting` | Owns audit export behavior while preserving snapshot consistency and no partial durable write on failure. |
| `reporting/pilot_reporting_export.py` | `reporting` | Owns pilot reporting export behavior while preserving snapshot-consistent export tests. |
| `restore_readiness.py` | `runtime` | Move only with restore readiness ownership and clean failed-restore state tests. |
| `restore_readiness_backup_restore.py` | `runtime` | Move only with backup/restore ownership and all-or-nothing restore tests. |
| `restore_readiness_projection.py` | `runtime` | Move only with restore projection derivation tests from authoritative state. |
| `reviewed_slice_policy.py` | `core` | Move only with reviewed-slice policy ownership and direct scope binding tests. |
| `runtime/__init__.py` | `runtime` | Package scaffold marker only; no runtime, readiness, restore, operation, or config module moves are approved by the marker. |
| `runtime_boundary.py` | `runtime` | Move only with runtime trust boundary ownership and untrusted-header tests. |
| `runtime_restore_readiness_diagnostics.py` | `runtime` | Move only with diagnostics ownership and no mixed-snapshot aggregation. |
| `service.py` | `core` | Keep the public facade import path stable until facade compatibility policy is superseded. |
| `service_composition.py` | `core` | Move only with service composition ownership and unchanged facade construction. |
| `service_snapshots.py` | `core` | Move only with snapshot ownership and snapshot-consistent read tests. |
| `structured_events.py` | `core` | Move only with structured event ownership and unchanged event payload semantics. |

## 5. Compatibility Shim Expectations

The public Python package name `aegisops_control_plane` remains unchanged throughout Phase 52.5.1 and later child issues unless a later accepted ADR explicitly approves a rename.

The outer `control-plane/` directory remains unchanged because it is the reviewed repository home for live control-plane application code, service bootstrapping, adapters, tests, and service-local documentation.

Legacy import paths remain available during migration through compatibility shims or direct re-export modules until all documented internal, CLI, HTTP, test, and operator callers have migrated.

Removing a legacy import path requires a later transition policy that lists the affected import path, replacement import path, caller evidence, deprecation window, focused regression test, and rollback path.

Compatibility shims must be narrow: they may re-export or delegate to the new owner, but they must not make Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, projections, summaries, or adapter state authoritative.

If caller evidence is incomplete, malformed, or ambiguous, the old import path stays available.

## 6. Deferred Renames

The public package rename is deferred because external and internal callers currently import `aegisops_control_plane`, and renaming it before compatibility evidence would create avoidable runtime and test breakage.

The outer directory rename is deferred because `control-plane/` is already the approved repository-structure baseline for live control-plane code and must stay distinct from `postgres/control-plane/` persistence-contract assets.

Phase 52.5.1 does not approve production module moves, import rewrites, package renames, directory renames, Wazuh profile work, Shuffle profile work, runtime behavior changes, deployment behavior changes, or authority-boundary changes.

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

- No production module is moved.
- No production import path is changed.
- No public package name is changed.
- No outer repository directory is changed.
- No runtime behavior, HTTP behavior, CLI behavior, deployment behavior, Wazuh behavior, Shuffle behavior, ticket behavior, assistant behavior, evidence behavior, ML behavior, reporting behavior, backup behavior, restore behavior, readiness behavior, or durable-state side effect is changed.
- No subordinate source becomes authoritative workflow truth.
