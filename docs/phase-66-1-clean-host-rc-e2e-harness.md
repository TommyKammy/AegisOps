# Phase 66.1 Clean-Host RC E2E Harness

- **Status**: Accepted as the Phase 66.1 clean-host RC E2E harness contract for release-candidate proof planning only.
- **Date**: 2026-06-08
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/phase-65-closeout-evaluation.md`, `docs/getting-started/first-user-journey.md`, `docs/getting-started/first-user-demo-report-export.md`
- **Related Issues**: #1397, #1398

This contract defines the Phase 66.1 clean-host RC E2E harness shape for the first release-candidate replacement-readiness journey. It binds the documented first-user stack path to one reviewed proof surface from setup through report export.

Phase 65 packaging evidence is input only. It can supply release-bundle, offline-bundle, upgrade, integrity, licensing, documentation, migration, limitation, design-partner template, verifier, and issue-lint context, but it does not satisfy the Phase 66.1 clean-host RC E2E harness by itself.

## 1. Harness Purpose

The harness proves that a documented clean-host profile can collect one bounded RC journey packet for `init -> up -> doctor -> seed-demo -> UI workflow -> report export`.

The harness is proof evidence only. It records required commands, operator-visible workflow steps, evidence fields, failure boundaries, verifier coverage, and non-claims for the RC journey. It does not implement production deployment automation, GA readiness, real design-partner success, production rollout readiness, broad SIEM/SOAR parity, hosted update service readiness, or autonomous workflow authority.

## 2. Clean-Host Profile

The clean-host profile must record these fields before the journey starts:

| Field | Required value or evidence | Failure boundary |
| --- | --- | --- |
| `journey_run_id` | Stable identifier for the reviewed RC E2E run. | Missing or reused run identifiers fail the harness. |
| `repository_revision` | Immutable repository revision for the harness run. | Mutable branch names fail the harness. |
| `profile` | `smb-single-node`. | Any other profile must be handled by a later contract. |
| `environment_class` | `clean-host-rc-e2e`. | Unlabeled local developer state fails the harness. |
| `runtime_env_reference` | Repo-relative placeholder such as `<runtime-env-file>`. | Workstation-local paths and raw secret material fail the harness. |
| `operator_role` | Human operator or maintainer role that performed the run. | Browser state or UI cache cannot stand in for operator identity. |
| `evidence_dir` | Repo-relative placeholder such as `<evidence-dir>`. | Untracked local paths cannot become proof evidence. |
| `phase65_input_references` | Phase 65 closeout and packaging artifacts consumed as subordinate input. | Phase 65 closure cannot satisfy RC E2E by inference. |

## 3. Required Journey Steps

The harness must cover every step in this order.

| Order | Required step | Evidence required | Failure boundary |
| --- | --- | --- | --- |
| 1 | `aegisops init --profile smb-single-node` | Command, profile, revision, generated placeholder summary, and preflight outcome. | Missing profile or unsafe prerequisite must fail closed. |
| 2 | `aegisops up --with-wazuh --with-shuffle` | Component start result for AegisOps, Wazuh, Shuffle, and proxy-facing access path. | Mocked, skipped, or blocked components must stay explicit. |
| 3 | `aegisops doctor` | Product health, Wazuh health, Shuffle health, queue readiness, evidence storage, and report export readiness. | Doctor output is readiness evidence only, not workflow truth. |
| 4 | `aegisops seed-demo` | Demo seed identifier, demo-only labels, sample alert references, and reset posture. | Demo data cannot become production, gate, or workflow truth. |
| 5 | Login | Operator role, selected profile, visible demo or RC labels, and access result. | Browser state and session state remain subordinate context. |
| 6 | Health review | Reviewed health records for AegisOps, Wazuh source health, Shuffle availability, AI posture, and supportability posture. | Dashboard status cannot replace AegisOps readiness records. |
| 7 | Queue item | Queue item identifier, source, severity, identity or asset context, and demo or RC label. | Queue text cannot create an alert without AegisOps admission. |
| 8 | Wazuh-origin signal inspection | Wazuh signal identifier, source-health reference, AegisOps alert identifier, admission review, and provenance link. | Raw Wazuh state remains subordinate detection signal evidence. |
| 9 | Case promotion | Case identifier, alert binding, human decision, and case status. | Wazuh, UI, ticket, or AI state cannot promote a case. |
| 10 | Evidence review | Evidence identifiers, freshness, provenance, binding to alert and case, and unavailable follow-up when missing. | Evidence systems remain subordinate custody context. |
| 11 | AI trace review | AI trace identifier, cited sources, advisory output, human accepted/rejected/unresolved decision, and refused autonomous action scope. | AI cannot approve, execute, reconcile, close, activate detectors, or define source truth. |
| 12 | Action request | Action request identifier, target, action class, policy, protected-state boundary, and required approval. | Request text alone cannot execute an action. |
| 13 | Approval | Approval decision identifier, approver role, separation from executor, scope, and timestamp. | Approval cannot be inferred from comments, tickets, or UI state. |
| 14 | Shuffle delegation receipt | Shuffle workflow identifier, delegated action request, execution receipt, callback or receipt reference, and mismatch handling. | Shuffle success cannot become reconciliation truth. |
| 15 | Reconciliation | Reconciliation identifier, approved request, execution receipt, compared result, mismatch outcome, and rollback or follow-up owner. | Reconciliation cannot be inferred from downstream status. |
| 16 | Report export | Export command, export artifact reference, schema version, redaction review, source record identifiers, and non-secret result. | Reports are derived surfaces and cannot replace source records. |
| 17 | Next-step guidance | Known limitations, blocker owner, supportability follow-up, Phase 66 continuation, and Phase 67 prerequisite reminder. | Next-step guidance cannot accept RC or GA gates by itself. |

## 4. Evidence Packet Fields

Every Phase 66.1 packet must include these field families:

| Family | Required fields | Authority rule |
| --- | --- | --- |
| Install evidence | `journey_run_id`, `repository_revision`, `profile`, `environment_class`, `runtime_env_reference`, `operator_role`, `evidence_dir`. | Install success is accepted only as setup evidence. |
| Wazuh signal evidence | `wazuh_signal_id`, `source_health_reference`, `aegisops_alert_id`, `admission_review_id`, `provenance_reference`. | Wazuh remains subordinate detection signal evidence. |
| Shuffle execution evidence | `shuffle_workflow_id`, `action_request_id`, `approval_decision_id`, `execution_receipt_id`, `reconciliation_id`. | Shuffle remains subordinate delegated execution evidence. |
| AI trace evidence | `ai_trace_id`, `citation_set`, `reviewed_recommendation_id`, `human_decision`, `autonomous_action_refusal`. | AI remains advisory-only evidence. |
| Report export evidence | `export_command`, `export_artifact_reference`, `report_schema_version`, `redaction_review_id`, `source_record_ids`. | Reports remain derived evidence surfaces. |
| Supportability evidence | `doctor_result_id`, `support_bundle_posture`, `backup_restore_posture`, `upgrade_plan_reference`, `known_limitation_ids`. | Supportability evidence cannot become gate truth. |
| Limitation evidence | `limitation_id`, `owner`, `accepted_or_refused_reason`, `decision_date`, `follow_up_date`. | Limitations remain explicit AegisOps-owned records. |

Missing, malformed, mixed-snapshot, placeholder-backed where a concrete reviewed identifier is required, or subordinate-authority evidence blocks the harness until it is supplied or explicitly refused with an owner and follow-up date.

## 5. Authority Boundary

AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

Wazuh, Shuffle, AI, reports, UI state, browser state, verifier output, issue-lint output, release artifacts, demo data, tickets, evidence systems, dashboards, support bundles, and downstream receipts remain subordinate context. They cannot approve, execute, reconcile, close, accept limitations, accept RC gates, accept GA gates, or become workflow truth by themselves.

The harness must reject missing journey steps, missing evidence fields, missing authority boundaries, missing limitations, workstation-local paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, self-service commercial readiness claims, production rollout readiness claims, broad SIEM/SOAR parity claims, verifier-as-readiness-truth, and issue-lint-as-readiness-truth.

## 6. Accepted Limitations

Phase 66.1 proves the harness shape and evidence contract for one bounded clean-host RC E2E path. It does not collect real design-partner evidence, prove real design-partner success, complete support-bundle review, complete restore dry-run proof, complete upgrade rehearsal proof, approve production rollout, approve self-service commercial readiness, or satisfy Phase 67 GA readiness.

Later Phase 66 issues must still prove Wazuh sample signal, Shuffle sample execution, AI-assisted triage, report export, supportability, authority-boundary negative tests, and closeout evidence independently.

## 7. Verification

Run `bash scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh`.

Run `bash scripts/test-verify-phase-66-1-clean-host-rc-e2e-harness.sh`.

Run `bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1398 --config <supervisor-config-path>`.
