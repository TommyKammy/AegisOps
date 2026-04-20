# AegisOps Control-Plane Service Internal Boundaries

This document defines the target internal decomposition for `control-plane/aegisops_control_plane/service.py` before follow-up extraction work begins.

It supplements `docs/control-plane-runtime-service-boundary.md`, `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md`, and `docs/phase-21-production-like-hardening-boundary-and-sequence.md`.

For the repo-wide rule that decides when a hotspot should move into another maintainability backlog instead of continuing to grow in place, see `docs/maintainability-decomposition-thresholds.md`.

This note is intentionally limited to internal service boundaries and extraction sequencing. It does not approve a broader runtime surface, new external APIs, or behavior changes outside the already-reviewed Phase 19-21 slice.

## 1. Purpose

`AegisOpsControlPlaneService` currently acts as one large application facade plus most of the implementation behind that facade.

That single file now owns multiple reviewed concerns:

- runtime bootstrap and reverse-proxy/auth fail-closed checks;
- Wazuh-backed and native-detection intake;
- analyst queue, alert detail, case detail, and casework mutation paths;
- assistant/advisory assembly and citation-grounded read shaping;
- action request creation, approval-bound delegation, and execution reconciliation;
- startup, shutdown, readiness, backup, restore, and restore-drill behavior; and
- Phase 19 slice policy boundaries that prevent out-of-scope operator and advisory reads.

The target decomposition must preserve the current Phase 19-21 reviewed behavior while making internal responsibilities explicit enough that later extraction issues do not invent new seams or weaken fail-closed checks.

## 2. Current Responsibility Clusters

The current `service.py` implementation naturally groups into the following responsibility clusters.

### 2.1 Runtime and Protected-Surface Boundary

This cluster includes runtime description, structured event logging, reverse-proxy trust checks, protected-surface authentication, administrative bootstrap, and break-glass secret validation.

Representative methods include:

- `describe_runtime`
- `validate_wazuh_ingest_runtime`
- `validate_protected_surface_runtime`
- `authenticate_protected_surface_request`
- `require_admin_bootstrap_token`
- `require_break_glass_token`
- `_wazuh_ingest_listener_is_loopback`
- `_is_trusted_wazuh_ingest_peer`
- `_is_trusted_protected_surface_peer`

### 2.2 Detection Intake and Alert Materialization

This cluster owns live Wazuh admission, native detection normalization, analytic-signal admission, alert creation or restatement, evidence attachment, and alert-to-case promotion inputs.

Representative methods include:

- `ingest_wazuh_alert`
- `ingest_native_detection_record`
- `_ingest_analytic_signal_admission`
- `_attach_native_detection_context`
- `_with_native_detection_admission_provenance`
- `ingest_finding_alert`
- `promote_alert_to_case`
- `_resolve_analytic_signal_id`
- `_link_case_to_analytic_signals`
- `_list_alert_evidence_records`
- `_link_case_to_alert_reconciliations`

### 2.3 Analyst Read Models and Casework Mutation

This cluster assembles the approved operator reads and bounded casework mutations for the first daily workflow.

Current extraction status as of issue `#633`:

- approved analyst queue and detail reads already live behind `OperatorInspectionReadSurface`; and
- bounded case mutation entrypoints now delegate from `AegisOpsControlPlaneService` into `CaseWorkflowService`.

Representative methods include:

- `inspect_analyst_queue`
- `inspect_alert_detail`
- `inspect_case_detail`
- `record_case_observation`
- `record_case_lead`
- `record_case_recommendation`
- `record_case_handoff`
- `record_case_disposition`
- `_observations_for_case`
- `_leads_for_case`
- `_validate_case_evidence_linkage`

### 2.4 Assistant and Advisory Assembly

This cluster builds citation-grounded assistant context, advisory output, recommendation drafts, and advisory attachments from reviewed control-plane records.

Representative methods include:

- `inspect_assistant_context`
- `inspect_advisory_output`
- `render_recommendation_draft`
- `attach_assistant_advisory_draft`
- `_assistant_action_lineage_ids`
- `_assistant_ai_trace_records_for_context`
- `_assistant_linked_evidence_ids`
- `_assistant_evidence_records_for_context`
- `_assistant_recommendation_records_for_context`
- `_assistant_reconciliation_records_for_context`

### 2.5 Action Governance, Delegation, and Reconciliation

This cluster owns action-policy evaluation, approval-bound action request creation, reviewed delegation to Shuffle or the isolated executor, execution correlation, and authoritative reconciliation state.

Representative methods include:

- `create_reviewed_action_request_from_advisory`
- `evaluate_action_policy`
- `delegate_approved_action_to_shuffle`
- `delegate_approved_action_to_isolated_executor`
- `reconcile_action_execution`
- `_normalize_observed_executions`
- `_find_authoritative_action_execution`
- `_load_approved_delegation_context`
- `_require_exact_approved_payload_binding`
- `_require_exact_approved_expiry_binding`
- `_determine_action_policy`

### 2.6 Runtime Readiness, Backup, and Restore

This cluster owns startup/readiness/shutdown views, authoritative backup export, restore validation, and restore-drill proof.

Representative methods include:

- `describe_startup_status`
- `describe_shutdown_status`
- `inspect_readiness_diagnostics`
- `_inspect_readiness_aggregates`
- `export_authoritative_record_chain_backup`
- `restore_authoritative_record_chain_backup`
- `run_authoritative_restore_drill`
- `_run_authoritative_restore_drill_snapshot`
- `_require_empty_authoritative_restore_target`
- `_validate_authoritative_record_chain_restore`

### 2.7 Phase 19 Slice Policy Boundaries

This cluster enforces the reviewed narrow live slice for operator and advisory behavior.

Representative methods include:

- `_require_phase19_operator_case`
- `_require_phase19_case_scoped_advisory_read`
- `_require_phase19_case_scoped_recommendation_payload`
- `_require_phase19_operator_case_record`
- `_case_is_in_phase19_operator_slice`
- `_phase19_operator_source_family`
- `_phase19_context_declares_out_of_scope_provenance`
- `_phase19_context_explicitly_declares_provenance`

## 3. Target Internal Collaborators

The target shape keeps `AegisOpsControlPlaneService` as a narrow orchestration facade while moving cohesive behavior behind internal collaborators with explicit dependency direction.

The target collaborators are:

- `RuntimeBoundaryService`
  Owns runtime description, structured event emission, reverse-proxy trust validation, protected-surface authentication, administrative bootstrap, and break-glass checks.
- `DetectionIntakeService`
  Owns Wazuh/native-detection admission, analytic-signal materialization, alert/evidence/case linkage during intake, and source-admission normalization.
- `AnalystWorkflowService`
  Owns analyst queue and detail read models plus bounded casework mutation paths for observations, leads, recommendations, handoff, disposition, and alert-to-case promotion.
- `CaseWorkflowService`
  Owns the bounded case mutation write path now extracted from `service.py`: observations, leads, recommendations, handoff, and disposition. This is the first extracted write-path slice inside the broader analyst workflow cluster and preserves the stable facade entrypoints on `AegisOpsControlPlaneService`.
- `AssistantAdvisoryService`
  Owns assistant-context assembly, citation-grounded lineage gathering, advisory output shaping, recommendation draft rendering, and advisory draft attachment.
- `ActionGovernanceService`
  Owns action-policy evaluation, action request creation, approval-bound delegation, observed-execution normalization, and action/delegation/reconciliation binding checks.
- `RestoreReadinessService`
  Owns startup/shutdown/readiness snapshots, backup export, restore validation, restore execution, and restore-drill proof.
- `Phase19Policy`
  Owns reusable policy decisions for the approved Phase 19 slice policy boundaries, including case eligibility, case-scoped advisory reads, and reviewed provenance checks.

## 4. Dependency Direction

The dependency direction must remain explicit and one-way:

- `AegisOpsControlPlaneService` depends on internal collaborators and remains the public facade.
- `RuntimeBoundaryService`, `DetectionIntakeService`, `AnalystWorkflowService`, `AssistantAdvisoryService`, `ActionGovernanceService`, and `RestoreReadinessService` may depend on shared store and adapter ports plus reusable policies.
- `AnalystWorkflowService`, `AssistantAdvisoryService`, `ActionGovernanceService`, and `RestoreReadinessService` may depend on `Phase19Policy` for reviewed-slice admission decisions.
- `DetectionIntakeService` may expose helper methods used by `AnalystWorkflowService` or `RestoreReadinessService` only through stable internal interfaces, not by reaching back through the facade.
- Collaborators must not depend on HTTP transport concerns, CLI entrypoints, or reverse-proxy header parsing outside `RuntimeBoundaryService`.
- Collaborators must not treat Shuffle, the isolated executor, Wazuh, or PostgreSQL as the authority for policy-sensitive workflow truth.

The intended graph is:

`AegisOpsControlPlaneService -> collaborator -> store/adapters/policies`

The reverse direction is not allowed. Helpers and policies must not call back upward into the facade.

## 5. Facade Responsibilities

`AegisOpsControlPlaneService remains the public facade` for the current runtime surface. Existing public methods stay on the facade for now so follow-up child issues can refactor internally without changing reviewed callers.

The facade should continue to expose:

- runtime and auth methods:
  `describe_runtime`, `validate_wazuh_ingest_runtime`, `validate_protected_surface_runtime`, `authenticate_protected_surface_request`, `require_admin_bootstrap_token`, `require_break_glass_token`
- intake and alert methods:
  `ingest_wazuh_alert`, `ingest_finding_alert`, `ingest_native_detection_record`, `promote_alert_to_case`
- analyst read and mutation methods:
  `inspect_analyst_queue`, `inspect_alert_detail`, `inspect_case_detail`, `record_case_observation`, `record_case_lead`, `record_case_recommendation`, `record_case_handoff`, `record_case_disposition`
- assistant/advisory methods:
  `inspect_assistant_context`, `inspect_advisory_output`, `render_recommendation_draft`, `attach_assistant_advisory_draft`
- action and reconciliation methods:
  `create_reviewed_action_request_from_advisory`, `evaluate_action_policy`, `delegate_approved_action_to_shuffle`, `delegate_approved_action_to_isolated_executor`, `reconcile_action_execution`
- readiness and restore methods:
  `describe_startup_status`, `describe_shutdown_status`, `inspect_readiness_diagnostics`, `inspect_records`, `inspect_reconciliation_status`, `export_authoritative_record_chain_backup`, `restore_authoritative_record_chain_backup`, `run_authoritative_restore_drill`

The facade should be responsible only for:

- constructing collaborators from the existing config, store, adapters, and logger;
- maintaining current public method names and signatures;
- forwarding calls into the correct collaborator;
- preserving transaction boundaries where a workflow spans multiple collaborators; and
- preserving current exception text and fail-closed behavior unless a follow-up issue explicitly narrows that change.

For the case mutation slice specifically, the current reviewed delegation path is:

`AegisOpsControlPlaneService.record_case_* -> CaseWorkflowService`

## 6. Shared Helper Placement Rules

Shared helper placement rules must stay strict so extraction work does not produce a second unreviewed `service.py` inside another module.

Helpers should stay `module-level` only when they are:

- pure data-shaping functions with no store, adapter, or logger dependency;
- shared by multiple collaborators;
- stable across reviewed workflow boundaries; and
- easier to reason about as standalone serialization, hashing, merge, redaction, or normalization helpers.

Examples that can remain module-level include:

- `_json_ready`
- `_record_to_dict`
- `_redacted_reconciliation_payload`
- `_approved_payload_binding_hash`
- `_merge_reviewed_context`
- `_dedupe_strings`
- `_find_duplicate_strings`
- `_derive_readiness_status`

Helpers should move behind collaborators when they:

- require store access;
- depend on adapter behavior;
- encode workflow-specific sequencing;
- are meaningful only within one collaborator boundary; or
- make a fail-closed decision that should live beside the owning workflow.

Examples that should move behind collaborators include:

- runtime peer-trust checks behind `RuntimeBoundaryService`
- evidence, recommendation, and reconciliation lineage gatherers behind `AssistantAdvisoryService`
- alert-to-case linkage and admission helpers behind `DetectionIntakeService`
- action binding and execution-correlation helpers behind `ActionGovernanceService`
- restore-target validation and restore-drill helpers behind `RestoreReadinessService`

Helpers should become a `reusable policy` when they:

- encode an approved business boundary rather than local implementation convenience;
- must be shared consistently by more than one collaborator; and
- must preserve a reviewed fail-closed decision across reads and writes.

The first reusable policy extracted from `service.py` should be `Phase19Policy`.

## 7. Boundary Preservation Rules

The decomposition must explicitly preserve the current Phase 19-21 reviewed behavior.

The preserved boundaries are:

- `assistant/advisory assembly` remains citation-grounded, advisory-only, case-scoped where required, and unable to mint approval or execution authority.
- `action/delegation/reconciliation` remains approval-bound, payload-hash-bound, expiry-bound, and authoritative inside AegisOps rather than Shuffle or executor-local state.
- `runtime/readiness/restore` remains narrow, review-oriented, and production-like only for the current approved live path.
- `Phase 19 slice policy boundaries` remain fail closed for out-of-scope sources, non-live provenance, missing case linkage, and uncited recommendation paths.

The extracted internal shape must not:

- broaden the reviewed operator surface;
- broaden the approved action catalog;
- broaden second-source admission beyond the reviewed sequence;
- turn helper extraction into a behavior rewrite; or
- weaken transaction or validation sequencing that currently causes the service to fail closed.

## 8. Safest Extraction Order

The safest extraction order is the one that separates low-risk structural moves from behavior-heavy policy and workflow moves.

The reviewed order for follow-up child issues is:

1. Extract `Phase19Policy`.
   This is the safest first move because it isolates the narrowest reviewed policy seam without changing adapter calls or persistence flow.
2. Extract `RuntimeBoundaryService`.
   Runtime/auth logic is cohesive, mostly independent from the record graph, and already guarded by explicit fail-closed checks.
3. Extract `RestoreReadinessService`.
   Readiness and restore logic forms a mostly self-contained operational boundary that can move without reopening analyst or action semantics.
4. Extract `AssistantAdvisoryService`.
   This is large but primarily read-oriented once `Phase19Policy` is available as a shared guardrail.
5. Extract `AnalystWorkflowService`.
   Queue and casework flows depend on established detail/read helpers and on Phase 19 policy enforcement, so they are safer after the prior read-oriented decomposition.
6. Extract `ActionGovernanceService`.
   This comes after advisory extraction because action request creation depends on advisory context, recommendation binding, and case-scoped policy checks.
7. Extract `DetectionIntakeService`.
   Intake and alert materialization interact with the largest amount of authoritative linking and reconciliation behavior, so this should move last after the other seams are explicit.

This order is designed to preserve dependency direction and reduce the risk of breaking current public method signatures while refactoring internal ownership.

## 9. Non-Goals

Non-Goals for this design are:

- changing public method names, public method signatures, or the current service entrypoint shape;
- splitting the runtime into separate deployable services;
- introducing a new analyst UI, new HTTP boundary, or new top-level repository root;
- broadening source families, action types, or topology scope beyond the reviewed Phase 19-21 path;
- replacing module-local pure helpers with premature framework abstractions; and
- reopening the already-reviewed fail-closed contracts for reverse-proxy auth, approval binding, reconciliation authority, or restore validation.

## 10. Implementation Guidance for Follow-Up Issues

Each follow-up extraction issue should:

- keep tests focused on one collaborator boundary at a time;
- preserve existing facade entrypoints on `AegisOpsControlPlaneService`;
- preserve current transaction scope unless the issue explicitly proves a safer narrower boundary;
- move policy logic before moving workflow logic that depends on that policy;
- avoid mixing helper relocation with behavior changes in the same patch; and
- verify that the resulting slice still aligns with the reviewed Phase 19-21 documents before merging.

This document is the decomposition contract for future `service.py` extraction work. Later issues may rename internal classes during implementation if the resulting ownership and dependency direction remain materially identical to the boundaries defined here.
