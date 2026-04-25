# Phase 33 Operational Evidence Retention and Audit Handoff Pack

## 1. Purpose and Boundary

This document defines the Phase 33 operational evidence retention and audit handoff pack for the reviewed single-customer profile.

The handoff pack is a small-team operational package, not a new archive platform, SIEM replacement, or external authority source.

The authoritative record chain remains inside AegisOps reviewed records for approval, evidence, execution, and reconciliation truth.

The pack is anchored to `docs/deployment/single-customer-release-bundle-inventory.md`, `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, and `docs/deployment/runtime-smoke-bundle.md`.

For the Phase 38 single-customer launch package, `docs/deployment/single-customer-release-bundle-inventory.md` is the reviewed bundle manifest that names this handoff pack as required retained evidence guidance.

Use this pack when an operator needs a compact, reviewable evidence bundle after deployment, upgrade, restore, approval, execution, reconciliation review, rollback, or a planned handoff window.

The pack may reference external substrate receipts, backup custody notes, or bounded logs, but those references remain evidence attached to reviewed AegisOps records. They do not create a parallel source of authority.

## 2. Retained Evidence Categories

| Event category | Retained evidence | Authority boundary |
| --- | --- | --- |
| Upgrade | Approved maintenance window, named operator, pre-change backup custody confirmation, selected restore point, before-and-after repository revisions, pre-change and post-change smoke results, bounded upgrade-window logs, and rollback decision. | Handoff evidence only; upgrade success is accepted only when the reviewed runtime checks and AegisOps record chain remain trustworthy. |
| Restore | Triggering reason, selected restore point, backup custody confirmation, repository revision or release identifier, post-restore readiness checks, and approval, evidence, execution, and reconciliation record-chain validation outcome. | Restore evidence supports return-to-service review but does not redefine record truth outside AegisOps. |
| Approval | Customer-scoped approver ownership, approval decision reference, reviewed case or action scope, timeout or rejection reason when applicable, and any break-glass custody note. | Approval truth remains the reviewed AegisOps approval record, not the handoff note. |
| Execution | Action request reference, approved execution surface, dispatch or refusal receipt, bounded executor or substrate receipt when present, and idempotency or correlation evidence needed for review. | Execution truth remains the AegisOps action-execution record and linked receipt, not vendor-local status alone. |
| Reconciliation | Reconciliation record reference, expected outcome, observed outcome, mismatch or terminal marker, reviewer decision, and linked evidence used to close or escalate the outcome. | Reconciliation truth remains the reviewed AegisOps reconciliation record. |

For deployment-only handoff where no approval, execution, or reconciliation event occurred, retain the startup, readiness, runtime inspection, smoke, backup custody, and named-operator evidence required by the runbook and single-customer profile.

For Phase 37 customer-like rehearsal, include the verifier result from `scripts/verify-customer-like-rehearsal-environment.sh --env-file <runtime-env-file>`, the reviewed record-chain replay result from `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`, and the executable smoke gate manifest from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` with the startup, backup-custody, and clean-state evidence.

For Phase 37 restore, rollback, and upgrade rehearsal, retain the release-gate manifest verified by `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>` so backup, restore, rollback, upgrade, smoke, reviewed-record, and clean-state evidence remain linked in one handoff index.

For failed, rejected, or refused events, retain the refusal reason and the clean-state confirmation. Do not replace a failed path with a later successful retry summary unless the failed outcome remains reviewable.

## 3. Operator-Visible Handoff Artifacts

The operator-visible artifacts are the maintenance or review record, runtime smoke result, backup and restore custody note, bounded logs with secrets redacted, readiness and runtime inspection outputs, and reviewed record-chain references.

Operator-visible artifacts should be compact enough for the next business-hours reviewer to answer four questions:

- what event happened and who owned it;
- which reviewed AegisOps record or repository revision anchors it;
- which evidence category entries prove the outcome; and
- what follow-up owner or next review must still act.

Saved artifacts must avoid live secrets, DSNs, customer credentials, bootstrap tokens, break-glass tokens, unsigned identity hints, sample credentials, and raw forwarded-header values that have not already been normalized by the reviewed boundary.

Bounded logs should preserve the relevant startup, upgrade, restore, execution, or reconciliation signal without becoming a raw log archive.

## 4. Minimal Handoff Package

The minimal handoff package after deployment, upgrade, restore, approval, execution, or reconciliation review contains:

- the reviewed event type and named operator;
- the repository revision or release identifier when the event changes runtime state;
- the customer-scoped scope reference without embedding live customer secrets;
- the required evidence category entries for the event;
- the runtime smoke result when deployment, upgrade, rollback, or handoff readiness is in scope;
- the backup, restore, or rollback custody reference when recovery state is in scope;
- the AegisOps reviewed record identifiers for approval, execution, evidence, or reconciliation when workflow truth is in scope; and
- the next daily queue, health review, restore review, or reconciliation follow-up owner.

The package can be a short maintenance note, ticket comment, reviewed runbook entry, or other operator-visible record if it preserves the required fields and links back to the authoritative AegisOps records.

The package should not duplicate full record payloads when stable AegisOps identifiers and redacted, bounded evidence references are sufficient for review.

## 5. Retention Expectations

Retention is bounded to the reviewed small-team operating need: keep the latest deploy or upgrade handoff, the latest successful restore rehearsal or restore event, open approval, execution, and reconciliation review evidence, and the evidence required for the next daily or weekly operator review.

Older handoff packs may be summarized or superseded after the reviewed follow-up is complete, provided the AegisOps reviewed records and required backup or restore custody evidence remain intact.

Evidence retention is event-oriented and review-oriented. It is not a promise to preserve every raw log line, every external substrate status, every runtime sample, or every historical smoke command forever.

If a review remains open, disputed, failed, or under reconciliation, retain the directly linked handoff evidence until the reviewed record reaches a clear terminal or escalation state.

## 6. Restore and Reconciliation Alignment

Retention expectations must remain aligned with the Phase 32 restore contract: approval, evidence, execution, and reconciliation records must return cleanly from the selected PostgreSQL-aware restore point before normal operation resumes.

The handoff pack must reference the Phase 33 runtime smoke bundle for deployment, upgrade, rollback, and operator handoff readiness evidence.

If restore, export, readiness, or detail rollup evidence appears to combine mixed snapshots, the handoff must stay blocked until operators can prove one committed state or preserve the refusal as the review outcome.

When reconciliation evidence exists, the handoff must point to the directly linked reconciliation record and its evidence. It must not generalize a mismatch, terminal marker, or reviewer decision to sibling records, nearby cases, or substrate-local status without an explicit authoritative link.

For recovery events, the handoff must include clean-state validation. It is not enough to record that an exception was raised or a restore command returned; the operator must preserve whether approval, evidence, execution, and reconciliation state remained intact and free of orphan or partial records.

## 7. Out of Scope

Enterprise SIEM archive design, unlimited retention, new authority sources, broad external archive integration, vendor-specific archive automation, multi-customer evidence warehouses, and raw secret-bearing evidence bundles are out of scope.

This pack also does not approve direct backend exposure, inferred customer binding, placeholder credentials, unreviewed forwarded headers, optional-extension prerequisites, or substrate-local status as authority for AegisOps approval, execution, or reconciliation truth.
