# AegisOps Phase 62.3 Per-Action Reconciliation Contract

This contract defines the reviewed receipt and reconciliation boundary for the Phase 62 default Read, Notify, and Soft Write catalog actions. It does not add new actions, launch Shuffle directly, widen SOAR marketplace scope, or treat downstream workflow success as AegisOps truth.

## Contract

Every reviewed Phase 62 action must carry expected receipt fields, correlation fields, and reconciliation outcomes in the action policy registry. The required outcomes are success, failure, missing, stale, mismatched, duplicated, wrong-correlation, and manual review.

The common receipt fields are `action_request_id`, `catalog_action`, `family`, `reviewed_template_version`, `correlation_id`, `idempotency_key`, `execution_run_id`, `started_at`, `finished_at`, and `status`. The common correlation fields are `action_request_id`, `approval_decision_id`, `delegation_id`, `execution_run_id`, `correlation_id`, `expected_execution_receipt_id`, and `idempotency_key`.

`enrichment_only_lookup` adds `lookup_subject_ref` and `lookup_evidence_ref` receipt metadata. `operator_notification` adds `recipient_ref`, `delivery_attempt_status`, and `normalized_receipt_ref`. `manual_escalation_request` adds `escalation_owner_ref`, `delivery_attempt_status`, and `fallback_needed`. `create_tracking_ticket` adds approval, ticket pointer, ticket system, ticket pointer custody, delivery status, normalized receipt, coordination reference, and coordination target correlation metadata.

## Enforcement Boundary

Shuffle receipts are subordinate evidence. A Shuffle `success` status can only update AegisOps action execution state when the observed receipt is bound to the authoritative AegisOps action request, approval decision, delegation, payload hash, workflow, workflow version, correlation identifier, expected receipt identifier, execution run, and idempotency key.

Missing receipt metadata, stale observations, mismatched surface/idempotency/binding values, duplicated unsafe observations, and wrong-correlation receipts reconcile as non-matched AegisOps reconciliation records. They do not mutate authoritative action execution records to succeeded, close cases, approve actions, or make downstream ticket or workflow state authoritative.

## Validation

Run `bash scripts/verify-phase-62-3-per-action-reconciliation-contract.sh`.

The focused validation covers:

- Per-action receipt metadata and correlation metadata in the Phase 62 registry.
- Notification reconciliation rejecting downstream success without a bound AegisOps receipt.
- Existing receipt normalization and tracking-ticket reconciliation behavior.
- Publishable path hygiene.
