# ADR-0013: Phase 52.5.2 Package Scaffolding and Compatibility-Shim Policy

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md`
- **Product**: AegisOps
- **Related Issues**: #1084, #1086
- **Depends On**: #1085
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Purpose

Phase 52.5.2 creates package markers for the target package families accepted in ADR-0012 before later child issues move modules.

The scaffolds are package markers only; they do not move production modules, rename `aegisops_control_plane`, or rename the outer `control-plane/` directory.

This policy records the compatibility-shim posture and layout guardrail skeleton that later package-migration issues must extend.

## 2. Target Package Scaffolds

The approved scaffold packages under `control-plane/aegisops_control_plane/` are:

| Package | ADR-0012 family | Posture |
| --- | --- | --- |
| `core/` | `core` | Package scaffold only; no production ownership move yet. |
| `api/` | `api` | Package scaffold only; no HTTP, CLI, or protected-surface move yet. |
| `runtime/` | `runtime` | Package scaffold only; no startup, config, readiness, or restore move yet. |
| `ingestion/` | `ingestion` | Package scaffold only; no detection lifecycle move yet. |
| `actions/` | `actions` | Package scaffold only; no action lifecycle or coordination move yet. |
| `actions/review/` | `actions.review` | Package scaffold retained as the owner for reviewed-action projection, visibility, timeline, chain, inspection, path health, coordination, index, and write-surface modules moved in Phase 52.5.4. |
| `evidence/` | `evidence` | Package scaffold only; no evidence boundary or facade move yet. |
| `assistant/` | `assistant` | Package scaffold retained as the owner for assistant context, advisory, provider, trace lifecycle, and workflow modules moved in Phase 52.5.3. |
| `ml_shadow/` | `ml_shadow` | Package scaffold only; no reviewed ML shadow-mode move yet. |
| `reporting/` | `reporting` | Package scaffold retained as the owner for audit and pilot reporting export modules moved in Phase 52.5.3. |

The existing `adapters/` package remains the approved adapter package marker from earlier phases.

## 3. Compatibility-Shim Policy

Legacy imports remain the stable public compatibility surface until a later child issue documents caller evidence, replacement imports, deprecation window, focused regression tests, and rollback path.

Compatibility shims may re-export from a new owner after a module move, but they must stay narrow and cannot introduce runtime behavior, durable-state side effects, or authority-boundary changes.

When caller evidence is missing, malformed, ambiguous, or only inferred from path shape, the legacy import path stays available.

Compatibility shims cannot make Wazuh, Shuffle, tickets, assistant output, generated config, CLI status, demo data, adapters, DTOs, projections, summaries, operator-facing text, or nearby metadata authoritative workflow truth.

Removing a legacy import path requires explicit caller evidence that covers internal imports, CLI imports, HTTP imports, tests, operator runbooks, and documented external usage where applicable.

## 4. Import Compatibility Checks

The initial import compatibility verifier covers `aegisops_control_plane.service:AegisOpsControlPlaneService` and `aegisops_control_plane.models:AlertRecord` as stable legacy imports.

Later child issues that move modules must add at least one legacy import check for each moved module before changing internal callers.

An import compatibility check that bypasses the legacy path and validates only the new package path is incomplete because it does not prove existing callers keep working.

Phase 52.5.3 extends the verifier so each moved assistant and reporting module is checked through both the legacy root import and the target package import:

- `aegisops_control_plane.ai_trace_lifecycle:AITraceLifecycleService`
- `aegisops_control_plane.assistant.ai_trace_lifecycle:AITraceLifecycleService`
- `aegisops_control_plane.assistant_advisory:AssistantAdvisoryCoordinator`
- `aegisops_control_plane.assistant.assistant_advisory:AssistantAdvisoryCoordinator`
- `aegisops_control_plane.assistant_context:AssistantContextAssembler`
- `aegisops_control_plane.assistant.assistant_context:AssistantContextAssembler`
- `aegisops_control_plane.assistant_provider:AssistantProviderAdapter`
- `aegisops_control_plane.assistant.assistant_provider:AssistantProviderAdapter`
- `aegisops_control_plane.live_assistant_workflow:LiveAssistantWorkflowCoordinator`
- `aegisops_control_plane.assistant.live_assistant_workflow:LiveAssistantWorkflowCoordinator`
- `aegisops_control_plane.audit_export:export_audit_retention_baseline`
- `aegisops_control_plane.reporting.audit_export:export_audit_retention_baseline`
- `aegisops_control_plane.pilot_reporting_export:export_pilot_executive_summary`
- `aegisops_control_plane.reporting.pilot_reporting_export:export_pilot_executive_summary`

Phase 52.5.4 extends the verifier so each moved action-review module is checked through both the legacy root import and the target `actions.review` package import:

- `aegisops_control_plane.action_review_chain:action_review_chains_for_scope`
- `aegisops_control_plane.actions.review.action_review_chain:action_review_chains_for_scope`
- `aegisops_control_plane.action_review_coordination:action_review_coordination_ticket_outcome`
- `aegisops_control_plane.actions.review.action_review_coordination:action_review_coordination_ticket_outcome`
- `aegisops_control_plane.action_review_index:build_action_review_record_index`
- `aegisops_control_plane.actions.review.action_review_index:build_action_review_record_index`
- `aegisops_control_plane.action_review_inspection:ActionReviewInspectionBoundary`
- `aegisops_control_plane.actions.review.action_review_inspection:ActionReviewInspectionBoundary`
- `aegisops_control_plane.action_review_path_health:action_review_path_health`
- `aegisops_control_plane.actions.review.action_review_path_health:action_review_path_health`
- `aegisops_control_plane.action_review_projection:build_action_review_record_index`
- `aegisops_control_plane.actions.review.action_review_projection:build_action_review_record_index`
- `aegisops_control_plane.action_review_timeline:action_review_timeline`
- `aegisops_control_plane.actions.review.action_review_timeline:action_review_timeline`
- `aegisops_control_plane.action_review_visibility:action_review_runtime_visibility`
- `aegisops_control_plane.actions.review.action_review_visibility:action_review_runtime_visibility`
- `aegisops_control_plane.action_review_write_surface:ActionReviewWriteSurface`
- `aegisops_control_plane.actions.review.action_review_write_surface:ActionReviewWriteSurface`

## 5. Layout Guardrail Skeleton

The layout guardrail skeleton rejects new flat root-level Python modules unless the Phase 52.5.1 inventory or the Phase 52.5.2 approved scaffold package set classifies them.

The guardrail intentionally accepts the current repository baseline after the scaffold markers are classified in ADR-0012.

Later child issues may extend the guardrail with package-family-specific rules only after the corresponding module moves and legacy import shims are verified.

## 6. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

Package scaffolding, compatibility shims, import verifiers, and layout guardrails are maintainability infrastructure only.

They do not change authorization, provenance, reconciliation, snapshot, backup, restore, export, readiness, assistant, evidence, action-execution, HTTP, CLI, deployment, Wazuh, Shuffle, ticket, ML, reporting, or durable-state behavior.

## 7. Validation

Run `bash scripts/verify-phase-52-5-2-package-scaffolding.sh`.

Run `bash scripts/verify-phase-52-5-2-import-compatibility.sh`.

Run `bash scripts/verify-phase-52-5-2-layout-guardrail.sh`.

Run `bash scripts/test-verify-phase-52-5-2-package-scaffolding-and-shim-policy.sh`.

Run `bash scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1086 --config <supervisor-config-path>`.

## 8. Non-Goals

- No production module is moved.
- No production import is rewritten.
- No public package name is changed.
- No outer repository directory is changed.
- No public API, runtime endpoint, CLI command, operator UI behavior, deployment behavior, or durable-state side effect is changed.
- No subordinate source, projection, DTO, summary, helper-module output, or nearby metadata becomes authoritative workflow truth.
