# Phase 58.5 Upgrade And Rollback Plan Contract

## Purpose

Phase 58.5 defines the reviewed upgrade plan and rollback plan evidence
contract for future AegisOps maintenance windows. The contract makes planning
evidence explicit before any automatic or silent upgrade behavior is considered.

Upgrade and rollback plans are reviewed planning evidence only. They do not run
upgrades, run rollbacks, mutate substrate state, approve release readiness,
replace Phase 51 gate evidence, or become authoritative AegisOps workflow,
release, gate, restore, or closeout truth.

## Runtime Surface

No live upgrade command, rollback command, scheduler, queue worker, substrate
adapter, database migration runner, Wazuh upgrader, or Shuffle upgrader is
introduced by this contract.

Future reviewed plans may be retained as Markdown or structured evidence, but
the only Phase 58.5 runtime posture is validation of the contract itself:

- Contract verifier: `bash scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh`.
- Focused verifier regression: `bash scripts/test-verify-phase-58-5-upgrade-rollback-plan-contract.sh`.
- Path hygiene: `bash scripts/verify-publishable-path-hygiene.sh`.
- Issue lint: `node <codex-supervisor-root>/dist/index.js issue-lint 1240 --config <supervisor-config-path>`.

## Required Plan Fields

| Field | Required content | Fail-closed rule |
| --- | --- | --- |
| `version_before` | Reviewed current AegisOps, profile, substrate, or package version before the proposed change. | Missing, floating, `latest`, beta, RC, TODO, or inferred versions fail. |
| `version_after` | Reviewed target AegisOps, profile, substrate, or package version after the proposed change. | Missing, floating, `latest`, beta, RC, TODO, or unreviewed target versions fail. |
| `target_profile` | Explicit reviewed deployment profile, product profile, substrate profile, or package profile affected by the plan. | Missing, guessed, path-derived, issue-title-derived, or operator-comment-derived profile binding fails. |
| `preflight_result` | Reviewed preflight evidence reference proving the current state is eligible for planning review. | Missing, failed, stale, placeholder, sample, or Wazuh-only preflight evidence fails. |
| `backup_reference` | Reviewed Phase 58.3 backup manifest or restore rehearsal reference used before the plan is considered reviewable. | Missing, placeholder, Wazuh-only, ticket-only, or inferred backup evidence fails. |
| `rollback_owner` | Named accountable owner or owner group for rollback decisions. | Missing, placeholder, sample, broad operator discretion, or inferred owner fails. |
| `rollback_trigger` | Reviewed condition that requires rollback review or rejects continued upgrade progress. | Missing, placeholder, broad operator discretion, TODO, or post-facto trigger definition fails. |
| `rollback_target` | Reviewed restore point, configuration revision, package revision, or profile revision to return to if rollback is triggered. | Missing, guessed, ticket-only, dashboard-only, or memory-derived rollback targets fail. |
| `known_limitations` | Reviewed limitations, non-goals, unsafe states, and retained manual steps for the proposed change. | Missing limitations or commercial-readiness, RC, GA, or replacement overclaims fail. |
| `evidence_links` | Links to AegisOps-owned release, restore, backup, source-health, smoke, or validation evidence records. | Missing links, Wazuh-only links, Shuffle-only links, ticket-only links, or operator-facing status text alone fails. |
| `authority_boundary` | Explicit statement that plans are subordinate planning evidence and cannot mutate substrate state or replace AegisOps truth. | Missing boundary or plan-as-authority claims fail. |

## Failure States

| State | Rejected condition | Required behavior |
| --- | --- | --- |
| `incompatible_version` | `version_before` or `version_after` is unsupported, floating, unreviewed, beta, RC, `latest`, or inconsistent with the target profile. | Reject the plan before upgrade scheduling or maintenance-window acceptance. |
| `missing_backup_evidence` | `backup_reference` is absent, placeholder-only, ticket-only, Wazuh-only, stale, or not tied to reviewed custody evidence. | Reject the plan before upgrade scheduling or maintenance-window acceptance. |
| `missing_rollback_owner` | Rollback owner is absent, TODO-only, sample-only, inferred from a team name, or broad operator discretion. | Reject the plan before any maintenance window is accepted. |
| `missing_rollback_trigger` | Rollback trigger is absent, placeholder-only, after-the-fact, or leaves rollback to vague operator judgment. | Reject the plan before any maintenance window is accepted. |
| `unsafe_plan_state` | Plan claims silent upgrade, automatic rollback, substrate mutation, release truth, gate truth, restore truth, workflow truth, or closeout truth. | Keep the guard in place and require a reviewed follow-up contract. |
| `placeholder_evidence` | Evidence links, owners, triggers, versions, preflight results, or rollback targets use TODO, sample, example, fake, guessed, or unsigned values. | Reject the plan until a trusted evidence source is supplied. |
| `plan_as_release_truth` | Plan evidence is used to approve release readiness, close a gate, close a workflow, prove restore success, or replace Phase 51 gate records. | Reject the plan and preserve authoritative AegisOps record-chain truth. |
| `substrate_mutation` | Plan review attempts to mutate Wazuh, Shuffle, PostgreSQL, OpenSearch, proxy, runtime config, schema, or package state. | Reject the operation; Phase 58.5 is planning evidence only. |

## Authority Boundary

Upgrade plans and rollback plans are subordinate planning evidence. AegisOps
control-plane records remain authoritative for alert, case, evidence, approval,
action request, execution receipt, reconciliation, audit, limitation, release,
gate, restore, workflow, and closeout truth.

Plan validation cannot approve release readiness, satisfy Pilot, Beta, RC, or GA
gates, prove live restore completion, prove upgrade success, approve substrate
mutation, close workflows, reconcile actions, or replace Phase 51 gate evidence.

When provenance, target profile, preflight, backup, rollback owner, rollback
trigger, evidence links, or authority-boundary signals are missing, malformed,
placeholder-like, or only partially trusted, validation fails closed.

## Negative Tests

The verifier must reject:

- silent upgrade claims;
- unsafe rollback claims;
- missing owner evidence;
- missing trigger evidence;
- placeholder evidence;
- plan-as-release-truth claims;
- substrate mutation claims;
- incompatible version claims;
- missing backup evidence;
- workstation-local absolute path guidance.

## Non-Goals

Phase 58.5 does not implement live upgrade execution, live rollback execution,
silent upgrade, automatic rollback, Wazuh broad upgrader behavior, Shuffle broad
upgrader behavior, release-gate automation, restore execution, database schema
migration, package migration, substrate mutation, support-bundle generation, or
customer-private evidence export.

## Validation

Run:

- `bash scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh`
- `bash scripts/test-verify-phase-58-5-upgrade-rollback-plan-contract.sh`
- `bash scripts/verify-publishable-path-hygiene.sh`
- `node <codex-supervisor-root>/dist/index.js issue-lint 1240 --config <supervisor-config-path>`
