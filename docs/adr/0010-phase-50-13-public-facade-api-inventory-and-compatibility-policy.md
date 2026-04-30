# ADR-0010: Phase 50.13 Public Facade API Inventory and Compatibility Policy

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #1030, #1031
- **Depends On**: #1022
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

Phase 50.12.7 records the accepted residual `service.py` closeout state before Phase 50.13 starts.

ADR-0003 remains authoritative for the public facade-preservation exception.

ADR-0004 through ADR-0009 remain authoritative unless a later accepted ADR explicitly supersedes a narrower maintainability decision.

`docs/maintainability-decomposition-thresholds.md` remains the governing hotspot trigger policy.

Phase 50.13 needs a repo-owned inventory before implementation slices continue so method-count reductions are driven by caller evidence, compatibility role, and authority-boundary ownership instead of arbitrary facade deletion.

This ADR does not remove, move, rename, or change any public `AegisOpsControlPlaneService` method.

## 2. Decision

Phase 50.13 classifies every current method defined directly on `AegisOpsControlPlaneService` by compatibility role and safe rewiring policy.

Later child issues may reduce facade method count only by proving that a method is not an external API, HTTP surface dependency, CLI dependency, documented compatibility delegate, or private guard that still belongs at the facade boundary.

AegisOps control-plane records remain authoritative workflow truth.

Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, snapshots, DTOs, and helper-module output remain subordinate context.

## 3. Starting Measurements

The Phase 50.12.7 starting measurements for `control-plane/aegisops_control_plane/service.py` are:

- `physical_lines=1451`
- `effective_lines=1294`
- `AegisOpsControlPlaneService methods=100`
- `phase=50.12.7`
- `issue=#1022`

The Phase 50.13 target ceiling is `AegisOpsControlPlaneService <= 85` methods if caller evidence proves the reduction is safe.

The long-term 50-method target remains out of scope for this ADR and requires later child issues with implementation evidence.

No baseline refresh is approved in this ADR because implementation slices remain.

## 4. Public Facade Inventory

Categories are intentionally conservative. A method with multiple callers is assigned to the most compatibility-sensitive current role. Private methods are classified by the boundary they currently guard, not by whether they might be extracted later.

| Method | Category | Caller / owner evidence | Phase 50.13 policy |
| --- | --- | --- | --- |
| `__init__` | internal-only | Service construction entrypoint. | Preserve facade initialization semantics while composition ownership stays internal. |
| `describe_runtime` | HTTP surface dependency | `/runtime`, CLI `runtime`, and runtime snapshot builder. | Retain public facade until HTTP and CLI callers share a stable alternate boundary. |
| `persist_record` | external API | Tests and internal workflows seed authoritative records through the facade. | Retain until callers have an explicit persistence boundary with identical lifecycle side effects. |
| `_lock_lifecycle_transition_subject` | private guard | Detection lifecycle helper compatibility. | Move only with lifecycle lock ownership. |
| `_linked_alert_case_lifecycle_lock_subject` | private guard | Detection lifecycle helper compatibility. | Move only with linked alert/case lifecycle lock ownership. |
| `_lifecycle_transition_id` | private guard | Detection lifecycle helper compatibility. | Move only with transition identity ownership. |
| `_initial_lifecycle_transitioned_at` | private guard | Detection lifecycle helper compatibility. | Move only with transition timestamp ownership. |
| `_reviewed_context_transitioned_at` | private guard | Detection intake helper compatibility. | Move only with reviewed-context transition ownership. |
| `_triage_disposition_matches_current_state` | private guard | Detection intake helper compatibility. | Move only with triage state ownership. |
| `_case_lifecycle_state_for_triage_disposition` | private guard | Detection intake helper compatibility. | Move only with case lifecycle state ownership. |
| `_latest_lifecycle_transition` | private guard | Detection lifecycle helper compatibility. | Move only with authoritative lifecycle read ownership. |
| `_lifecycle_transition_attribution` | private guard | Detection lifecycle helper compatibility. | Move only with lifecycle attribution ownership. |
| `list_lifecycle_transitions` | external API | Authoritative lifecycle inspection facade. | Retain until lifecycle inspection callers have a documented replacement. |
| `_emit_structured_event` | internal-only | Service-local structured logging helper. | May move with structured event ownership if event payload semantics remain unchanged. |
| `_emit_action_execution_delegated_event` | internal-only | Action delegation structured event helper. | May move with delegation event ownership if emitted fields remain unchanged. |
| `get_record` | external API | Tests and workflows read authoritative records through the facade. | Retain until callers have an explicit read boundary with identical record semantics. |
| `validate_wazuh_ingest_runtime` | external API | Runtime readiness and ingest validation boundary. | Retain while runtime validation remains public service behavior. |
| `validate_protected_surface_runtime` | external API | Runtime readiness and protected-surface validation boundary. | Retain while runtime validation remains public service behavior. |
| `authenticate_protected_surface_request` | external API | Protected-surface authentication boundary. | Retain and fail closed on untrusted headers or missing trusted proxy context. |
| `require_admin_bootstrap_token` | external API | Admin bootstrap authorization boundary. | Retain until a public auth boundary replaces it without accepting placeholders. |
| `require_break_glass_token` | external API | Break-glass authorization boundary. | Retain until a public auth boundary replaces it without accepting placeholders. |
| `ingest_wazuh_alert` | external API | Wazuh ingest runtime entrypoint. | Retain while Wazuh admission remains a service-facing API. |
| `_listener_is_loopback` | private guard | Runtime boundary helper compatibility. | Move only with listener trust evaluation ownership. |
| `_is_trusted_wazuh_ingest_peer` | private guard | Runtime boundary helper compatibility. | Move only with Wazuh peer trust enforcement. |
| `_is_trusted_protected_surface_peer` | private guard | Runtime boundary helper compatibility. | Move only with protected-surface peer trust enforcement. |
| `_is_trusted_peer_for_proxy_cidrs` | private guard | Runtime boundary helper compatibility. | Move only with trusted proxy CIDR enforcement. |
| `_peer_addr_is_loopback` | private guard | Runtime boundary helper compatibility. | Move only with peer address normalization ownership. |
| `delegate_approved_action_to_shuffle` | external API | Action execution delegation facade. | Retain until direct callers use the action lifecycle write boundary. |
| `delegate_approved_action_to_isolated_executor` | external API | Action execution delegation facade. | Retain until direct callers use the action lifecycle write boundary. |
| `evaluate_action_policy` | external API | Action policy evaluation facade. | Retain until policy evaluation has a public replacement preserving persisted review state. |
| `inspect_records` | CLI dependency | CLI `inspect-records`. | Retain until CLI no longer depends on the service facade. |
| `inspect_reconciliation_status` | CLI dependency | CLI `inspect-reconciliation-status`. | Retain until CLI no longer depends on the service facade. |
| `export_audit_retention_baseline` | external API | Audit retention export facade. | Retain until audit export callers use a documented export boundary. |
| `describe_startup_status` | CLI dependency | CLI `startup-status`. | Retain until CLI no longer depends on the service facade. |
| `describe_shutdown_status` | CLI dependency | CLI `shutdown-status`. | Retain until CLI no longer depends on the service facade. |
| `inspect_readiness_diagnostics` | HTTP surface dependency | `/diagnostics/readiness` and CLI readiness use. | Retain until HTTP and CLI callers share a stable alternate boundary. |
| `control_plane_change_authority_freeze_status` | external API | Control-plane change authority status boundary. | Retain unless change-authority callers move to an explicit authority service. |
| `_require_control_plane_change_authority_unfrozen` | private guard | Authority-sensitive progression guard. | Move only with authoritative change-freeze enforcement. |
| `_inspect_readiness_aggregates` | private guard | Restore/readiness helper compatibility. | Move only with readiness aggregate ownership. |
| `export_authoritative_record_chain_backup` | CLI dependency | CLI `backup-authoritative-record-chain`. | Retain until CLI no longer depends on the service facade. |
| `restore_authoritative_record_chain_backup` | CLI dependency | CLI `restore-authoritative-record-chain`. | Retain until CLI no longer depends on the service facade and failed restores remain clean. |
| `_restore_drill_snapshot_transaction` | private guard | Restore drill snapshot boundary. | Move only with snapshot-consistent restore drill ownership. |
| `run_authoritative_restore_drill` | CLI dependency | CLI `run-authoritative-restore-drill`. | Retain until CLI no longer depends on the service facade. |
| `_run_authoritative_restore_drill_snapshot` | private guard | Restore/readiness helper compatibility. | Move only with restore drill snapshot ownership. |
| `inspect_analyst_queue` | CLI dependency | CLI `inspect-analyst-queue`. | Retain until CLI no longer depends on the service facade. |
| `inspect_alert_detail` | CLI dependency | CLI `inspect-alert-detail`. | Retain until CLI no longer depends on the service facade. |
| `inspect_assistant_context` | CLI dependency | CLI `inspect-assistant-context`. | Retain until CLI no longer depends on the service facade. |
| `inspect_case_detail` | CLI dependency | CLI `inspect-case-detail`. | Retain until CLI no longer depends on the service facade. |
| `inspect_action_review_detail` | external API | Action-review detail inspection facade. | Retain until consumers use an explicit operator inspection boundary. |
| `record_action_review_manual_fallback` | CLI dependency | CLI `record-action-review-manual-fallback`. | Retain until CLI no longer depends on the service facade. |
| `record_action_review_escalation_note` | CLI dependency | CLI `record-action-review-escalation-note`. | Retain until CLI no longer depends on the service facade. |
| `inspect_advisory_output` | CLI dependency | CLI `inspect-advisory-output`. | Retain until CLI no longer depends on the service facade. |
| `render_recommendation_draft` | CLI dependency | CLI `render-recommendation-draft`. | Retain until CLI no longer depends on the service facade. |
| `run_live_assistant_workflow` | CLI dependency | CLI `run-live-assistant-workflow`. | Retain until CLI no longer depends on the service facade. |
| `create_reviewed_action_request_from_advisory` | CLI dependency | CLI `create-reviewed-action-request`. | Retain until CLI no longer depends on the service facade. |
| `create_reviewed_tracking_ticket_request_from_advisory` | external API | Tracking-ticket action request facade. | Retain until direct callers use the action lifecycle write boundary. |
| `record_action_approval_decision` | external API | Action approval decision facade. | Retain until callers use the action lifecycle write boundary. |
| `attach_assistant_advisory_draft` | external API | Advisory draft attachment facade. | Retain until callers use the assistant advisory boundary directly. |
| `_reconciliation_has_detection_lineage` | private guard | Detection reconciliation resolver compatibility. | Move only with authoritative detection lineage ownership. |
| `_latest_detection_reconciliation_for_alert` | private guard | Detection reconciliation resolver compatibility. | Move only with authoritative alert reconciliation ownership. |
| `_latest_detection_reconciliations_by_alert_id` | private guard | Detection reconciliation resolver compatibility. | Move only with snapshot-consistent reconciliation ownership. |
| `_reconciliation_is_wazuh_origin` | private guard | Detection reconciliation resolver compatibility. | Move only with origin validation ownership. |
| `_require_aware_datetime` | private guard | Shared input validation guard. | Move only when receiving boundary owns timestamp validation. |
| `_require_non_empty_string` | private guard | Shared input validation guard. | Move only when receiving boundary owns string validation. |
| `_normalize_optional_string` | private guard | Shared input normalization guard. | Move only when receiving boundary owns optional string normalization. |
| `_resolve_new_record_identifier` | private guard | Shared record identifier guard. | Move only when receiving boundary owns identifier allocation and collision checks. |
| `ingest_finding_alert` | compatibility delegate | Detection intake compatibility entrypoint retained after extraction. | Retain until documented callers use `DetectionIntakeService` safely. |
| `promote_alert_to_case` | CLI dependency | CLI `promote-alert-to-case`. | Retain until CLI no longer depends on the service facade. |
| `ingest_native_detection_record` | external API | Native detection adapter facade. | Retain until adapter callers use a documented detection intake boundary. |
| `reconcile_action_execution` | compatibility delegate | Action execution reconciliation compatibility entrypoint retained after extraction. | Retain until documented callers use the action lifecycle write boundary safely. |
| `_merge_linked_ids` | private guard | Evidence/linkage helper compatibility. | Move only with linked-id merge ownership. |
| `_linked_id_exists` | private guard | Evidence/linkage helper compatibility. | Move only with linked-id existence ownership. |
| `_require_empty_authoritative_restore_target` | private guard | Restore validation guard. | Move only with restore target cleanliness enforcement. |
| `_validate_authoritative_record_chain_restore` | private guard | Restore validation guard. | Move only with all-or-nothing record-chain restore ownership. |
| `_require_case_record` | private guard | Case lookup guard. | Move only with authoritative case read ownership. |
| `_require_action_request_record` | private guard | Action request lookup guard. | Move only with authoritative action-request read ownership. |
| `_require_reviewed_operator_case` | private guard | Reviewed slice policy guard. | Move only with reviewed operator case scope ownership. |
| `_require_single_linked_case_id` | private guard | Advisory/action binding guard. | Move only with explicit case binding ownership. |
| `_require_single_recommendation_binding` | private guard | Advisory/action binding guard. | Move only with explicit recommendation binding ownership. |
| `_require_reviewed_case_scoped_advisory_read` | private guard | Reviewed slice advisory guard. | Move only with reviewed advisory read ownership. |
| `_require_reviewed_alert_scoped_queue_summary_read` | private guard | Reviewed slice queue summary guard. | Move only with reviewed queue summary ownership. |
| `_reviewed_case_scoped_read_error` | private guard | Reviewed slice error helper. | Move only with reviewed case-scope policy ownership. |
| `_require_reviewed_case_scoped_recommendation_payload` | private guard | Reviewed slice recommendation guard. | Move only with reviewed recommendation payload ownership. |
| `_reviewed_operator_source_family` | private guard | Reviewed slice provenance helper. | Move only with reviewed source-family ownership. |
| `_reviewed_context_explicitly_declares_provenance` | private guard | Reviewed slice provenance helper. | Move only with reviewed provenance declaration ownership. |
| `_require_reviewed_operator_case_record` | private guard | Reviewed slice case guard. | Move only with reviewed operator case ownership. |
| `_require_reviewed_operator_alert_record` | private guard | Reviewed slice alert guard. | Move only with reviewed operator alert ownership. |
| `_case_is_in_reviewed_operator_slice` | private guard | Reviewed slice case predicate. | Move only with reviewed operator slice ownership. |
| `_alert_is_in_reviewed_operator_slice` | private guard | Reviewed slice alert predicate. | Move only with reviewed operator slice ownership. |
| `_reviewed_context_declares_out_of_scope_provenance` | private guard | Reviewed slice provenance guard. | Move only with out-of-scope provenance ownership. |
| `_normalize_linked_record_ids` | private guard | Evidence linkage guard. | Move only with linked record normalization ownership. |
| `_validate_case_evidence_linkage` | private guard | Evidence linkage guard. | Move only with case evidence linkage ownership. |
| `_validate_alert_evidence_linkage` | private guard | Evidence linkage guard. | Move only with alert evidence linkage ownership. |
| `_observations_for_case` | private guard | Case detail read helper. | Move only with snapshot-consistent case detail ownership. |
| `_leads_for_case` | private guard | Case detail read helper. | Move only with snapshot-consistent case detail ownership. |
| `_case_lifecycle_for_disposition` | private guard | Case lifecycle helper. | Move only with case lifecycle disposition ownership. |
| `_next_identifier` | private guard | Identifier allocation helper. | Move only with receiving boundary identifier ownership. |
| `_alert_review_state` | private guard | Alert detail projection helper. | Move only with alert review projection ownership. |
| `_alert_escalation_boundary` | private guard | Alert detail projection helper. | Move only with alert escalation projection ownership. |
| `_require_mapping` | private guard | Internal facade and extracted helpers. | Keep until receiving collaborator owns input-shape enforcement. |

No current method is classified as `test-only`. Tests exercise many compatibility entrypoints, but Phase 50.13 does not treat test usage alone as permission to delete a method when CLI, HTTP, external API, compatibility, or private guard evidence still exists.

## 5. Compatibility Delegate Policy

A method may be rewired away from the facade only when no external API, HTTP surface, CLI surface, or documented compatibility caller depends on the facade entrypoint.

A retained compatibility delegate must remain a narrow single-hop facade over an extracted authoritative boundary.

Private guards may move only when the receiving collaborator already owns the authoritative record, scope, provenance, authentication, or lifecycle boundary that the guard enforces.

Internal rewiring must preserve snapshot consistency for multi-record reads and all-or-nothing durable writes for logical mutations.

Later implementation slices must prove the directly linked caller set before removing a facade method. Naming conventions, path shape, comments, nearby metadata, sibling records, summary text, DTOs, and projection fields are not caller evidence.

If caller evidence is incomplete, malformed, or ambiguous, the method stays on the facade until the missing binding is resolved.

If a failed removal, restore, export, backup, readiness, or detail aggregation path rejects work, tests must also prove that no orphan record, partial durable write, or half-restored state survives the rejected path.

## 6. Validation

Run `bash scripts/verify-phase-50-13-public-facade-inventory-contract.sh`.

Run `bash scripts/test-verify-phase-50-13-public-facade-inventory-contract.sh`.

Run `bash scripts/verify-maintainability-hotspots.sh`.

Run `bash scripts/test-verify-maintainability-hotspots.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1031 --config <supervisor-config-path>`.

For the Phase 50.13 Epic, run the same issue-lint command for each Phase 50.13 child issue before allowing implementation slices to proceed.

## 7. Non-Goals

- No production code extraction is approved by this ADR.
- No public API, runtime endpoint, CLI command, operator UI behavior, or durable-state side effect is changed.
- No approval, execution, reconciliation, assistant, detection, external-evidence, restore, readiness, or operator authority behavior is changed.
- No ticket, ML, endpoint, network, browser, optional-evidence, Wazuh, Shuffle, Zammad, deployment, database, migration, credential source, HTTP surface, CLI surface, or operator UI behavior is changed.
- No baseline refresh is approved while Phase 50.13 implementation slices remain.
- No subordinate source, projection, DTO, summary, helper-module output, or nearby metadata becomes authoritative workflow truth.
- No long-term 50-method completion claim is approved unless later child issues prove it safely.

## 8. Approval

- **Proposed By**: Codex for Issue #1031
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-30
