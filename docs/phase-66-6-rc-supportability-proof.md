# Phase 66.6 RC Supportability Proof

- **Status**: Accepted as the Phase 66.6 RC supportability proof contract for release-candidate evidence planning only.
- **Date**: 2026-07-21 Asia/Tokyo
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-66-1-clean-host-rc-e2e-harness.md`, `docs/phase-58-3-backup-command-contract.md`, `docs/phase-58-4-restore-dry-run-contract.md`, `docs/phase-58-5-upgrade-rollback-plan-contract.md`, `docs/phase-58-6-support-bundle-redaction-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/phase-65-closeout-evaluation.md`
- **Related Issues**: #1397, #1403

This contract defines the Phase 66.6 RC supportability proof surface. It binds reviewed backup, restore dry-run, upgrade-plan, rollback-plan, support-bundle, redaction, owner-review, known-limitation, and non-claim evidence to one Phase 66 journey and one immutable repository revision.

The proof depends on the Phase 66.1 clean-host RC E2E harness and the Phase 58 supportability contracts. Those earlier artifacts remain input evidence only; they do not independently satisfy this proof or any RC, GA, production-support, customer-portal, or commercial-replacement gate.

## 1. Proof Purpose

The RC supportability proof demonstrates that the reviewed Phase 66 journey can assemble subordinate recovery, change-planning, diagnostic, redaction, ownership, and limitation evidence for RC review without treating support artifacts as workflow, release, gate, restore, limitation, audit, readiness, or closeout truth.

This proof is RC evidence only. It is not an RC gate pass, GA readiness, a production SLA commitment, a 24x7 support model, customer portal readiness, real design-partner support success, live restore completion, live upgrade or rollback completion, or commercial replacement readiness.

## 2. RC Supportability Evidence

Every Phase 66.6 proof packet must include these fields:

| Field | Required evidence | Failure boundary |
| --- | --- | --- |
| `journey_run_id` | The Phase 66.1 run identifier that observed the supportability evidence set. | Missing, placeholder, or mismatched journey identifiers fail the proof. |
| `repository_revision` | One immutable 40-character repository revision shared by the evidence set. | Mutable branches, tags, abbreviated revisions, or mixed revisions fail the proof. |
| `backup_evidence` | Reviewed backup manifest identity, custody reference, creation timestamp, owner, and completed status. | A manifest alone cannot prove restore success or release readiness. |
| `restore_dry_run_evidence` | Reviewed dry-run identity, source backup reference, target profile, timestamp, operator, and passed result. | Dry-run output cannot prove live restore completion or mutate authoritative records. |
| `upgrade_plan` | Reviewed plan identity, exact before and after versions, target profile, passed preflight reference, and AegisOps evidence links. | Floating versions, missing preflight evidence, or plan-as-release-truth claims fail the proof. |
| `rollback_plan` | Reviewed plan identity, backup reference, accountable rollback owner, trigger, and rollback target. | Missing ownership, vague triggers, or plan-driven substrate mutation fail the proof. |
| `support_bundle` | Reviewed bundle identity, environment class, component versions, doctor summary, backup/restore references, upgrade/rollback references, timestamp, owner, and AegisOps evidence links. | Missing provenance, mixed snapshots, or bundle-as-truth claims fail the proof. |
| `redaction_manifest` | Reviewed manifest identity, passed scan result, all Phase 58.6 redaction families, and explicit subordinate-evidence boundary. | Secret, credential, customer-private, ticket-private, token, header, certificate, or workstation-path leakage fails the proof. |
| `owner_review` | Reviewer, review timestamp, disposition, accepted-risk posture, and follow-up owner. | Missing review, self-approval by an artifact, or unowned follow-up fails the proof. |
| `limitation_references` | Known limitation ids, owner, decision date, and follow-up date for incomplete evidence. | Hidden, missing, or unowned limitations fail the proof. |
| `non_claims` | Explicit `rc-evidence-only`, `not-rc-gate-pass`, `not-ga`, `not-production-support`, `not-customer-portal`, `not-commercial-replacement`, and `not-support-truth` labels. | Missing labels or positive readiness claims fail the proof. |

A proof packet is fail-closed: once any required field is materialized, every required field must be present, non-placeholder, internally complete, and bound to the same journey run and immutable repository revision.

## 3. Evidence Binding And Secret Hygiene

Every structured evidence value must include the packet's exact `journey_run_id` and `repository_revision`; implicit binding through names, paths, or ticket context is not accepted.

The `backup_evidence` value must include `journey_run_id`, `repository_revision`, `manifest_id`, `custody_reference`, `created_at`, `owner`, and `status=completed`. Accountable people and groups must use explicit `person:<id>` or `group:<id>` identities; broad operator labels and automated identities are not accepted. The backup manifest remains subordinate custody evidence and cannot prove restore success.

The `restore_dry_run_evidence` value must include `journey_run_id`, `repository_revision`, `dry_run_id`, `evidence_reference`, `backup_reference`, `target_profile`, `created_at`, `operator`, and `result=passed`. Its timestamp must not predate the referenced backup. Restore dry-run output is preflight evidence only and cannot prove live restore completion.

The `upgrade_plan` value must include `journey_run_id`, `repository_revision`, `plan_id`, `evidence_reference`, `version_before`, `version_after`, `target_profile`, `preflight_result`, and `evidence_links`. Versions must be exact stable semantic versions; prerelease labels remain forbidden even when placed in build metadata. The `rollback_plan` value must include `journey_run_id`, `repository_revision`, `plan_id`, `evidence_reference`, `backup_reference`, `rollback_owner`, `rollback_trigger`, and `rollback_target`. A rollback trigger must be `failed:`, `rejected:`, or `threshold-breached:` followed by one direct AegisOps evidence URI. Plans are subordinate planning evidence and cannot perform or prove live substrate mutation.

The `support_bundle` value must include `journey_run_id`, `repository_revision`, `bundle_id`, `evidence_reference`, `environment_class`, `component_versions`, `doctor_summary`, `backup_restore_references`, `upgrade_rollback_references`, `created_at`, `owner`, and `evidence_links`. `backup_restore_references` must exactly identify the packet's backup custody and restore dry-run records, and `upgrade_rollback_references` must exactly identify its upgrade and rollback records. Every comma-delimited component entry must pair a component name with an exact stable semantic version, and the bundle timestamp must not predate its restore evidence. The bundle must use one committed snapshot and direct AegisOps evidence references; ticket-only, Wazuh-only, Shuffle-only, browser-only, UI-only, and operator-memory-only references fail.

The `redaction_manifest` value must include `journey_run_id`, `repository_revision`, `manifest_id`, `evidence_reference`, `bundle_reference`, `scan_result=passed`, `secret_values`, `workstation_paths`, `private_payloads`, `ticket_private_content`, `tokens_and_headers`, `certs_and_keys`, `credentials`, `customer_identifiers`, and `authority_boundary=subordinate-evidence-only`. Its bundle reference must match the packet's support bundle. Each redaction family must be `redacted`, `absent`, or `passed`. A redaction marker is safe only when it is the complete assigned value; retained evidence must not contain recoverable secrets, raw credentials, customer-private payloads, private ticket content, authorization material, certificates, keys, or workstation-local paths.

The `owner_review` value must include `journey_run_id`, `repository_revision`, `reviewer`, `reviewed_references`, `reviewed_at`, `disposition`, `accepted_risk`, and `follow_up_owner`. Its reviewed references must exactly identify the packet's support bundle and redaction manifest, and its timestamp must not predate the support bundle. Allowed dispositions are `accepted`, `accepted-with-follow-up`, and `rejected`; only explicit accountable person or group identities may review, and artifacts, bots, service identities, verifiers, issue-lint output, support bundles, and plans cannot review or approve themselves.

Materialized evidence timestamps must be no more than 24 hours old at verification time and must not be more than five minutes in the future. The backup, restore dry-run, support-bundle, and owner-review timestamps remain subject to their chronological ordering rules within that freshness window.

The `limitation_references` value must include `journey_run_id`, `repository_revision`, `ids`, `owner`, `decision_date`, and `follow_up_date`. The follow-up date must not predate the limitation decision. Missing or rejected evidence remains an owned limitation; it cannot be converted into a pass by absence, inference, verifier output, issue-lint output, or support-bundle generation.

## 4. Authority Boundary

AegisOps records remain authoritative for workflow, release, gate, restore acceptance, limitation, audit, approval, action request, execution receipt, reconciliation, source admission, and closeout truth.

Backup manifests, restore dry-run output, upgrade plans, rollback plans, support bundles, redaction manifests, owner-review summaries, limitation lists, verifier output, issue-lint output, browser state, UI cache, tickets, and optional evidence remain subordinate evidence. They cannot approve, execute, reconcile, close, release, gate, restore, mutate, promote, or replace AegisOps records.

The proof must reject missing or partial evidence packets, mixed revisions, stale or failed evidence, placeholder values, secret leakage, raw credential leakage, customer-private data, ticket-private content, authorization material, certificate or key material, workstation-local paths, support-bundle-as-truth claims, support-operator authority expansion, live restore claims, live upgrade or rollback claims, inferred RC pass, inferred GA pass, production SLA commitments, 24x7 support claims, customer portal claims, real design-partner support claims, commercial replacement claims, verifier-as-readiness-truth, and issue-lint-as-readiness-truth.

## 5. Accepted Limitations

Phase 66.6 records one repository-scoped supportability proof contract and focused verifier. It does not conduct a destructive restore, execute a live upgrade or rollback, operate a production support service, commit to a production SLA or 24x7 response model, create a customer portal, perform a real design-partner support review, retain production secrets, or complete the Phase 66 RC authority-boundary proof pack and closeout.

Later Phase 66 issues must still prove the RC authority-boundary proof pack and closeout evidence independently. Phase 67 must still evaluate GA readiness using its own accepted gate evidence.

## 6. Verification

Run `bash scripts/verify-phase-66-6-rc-supportability-proof.sh`.

Run `bash scripts/test-verify-phase-66-6-rc-supportability-proof.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1403 --config <supervisor-config-path>`.
