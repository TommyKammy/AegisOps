# Phase 66.7 RC Authority-Boundary Proof Pack

**Status**: Accepted as the Phase 66.7 RC authority-boundary proof-pack contract for release-candidate evidence planning only.

**Date**: 2026-07-23

**Related Issues**: #1397, #1404

## 1. Purpose And Evidence Inputs

This contract defines the Phase 66.7 RC authority-boundary proof pack.

The proof pack depends on the Phase 66.1-66.6 proof surfaces and the Phase 51.6 authority-boundary negative-test policy. It collects their evidence under one run and revision; it does not replace, reinterpret, or independently satisfy those contracts.

The required repository-owned inputs are:

- `docs/phase-66-1-clean-host-rc-e2e-harness.md`
- `docs/phase-66-2-wazuh-sample-signal-rc-proof.md`
- `docs/phase-66-3-shuffle-sample-execution-rc-proof.md`
- `docs/phase-66-4-ai-assisted-triage-rc-proof.md`
- `docs/phase-66-5-report-export-rc-proof.md`
- `docs/phase-66-6-rc-supportability-proof.md`
- `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`
- `docs/phase-65-closeout-evaluation.md`

This proof pack is RC evidence only. It cannot grant an RC gate pass, a GA gate pass, production authority, production rollout readiness, commercial replacement readiness, or broad enterprise SIEM/SOAR parity.

## 2. Required Proof Packet

Every materialized Phase 66.7 proof packet must include exactly one value for every field below:

| Field | Required evidence | Fail-closed rule |
| --- | --- | --- |
| `journey_run_id` | The Phase 66.1 journey run shared by every collected proof and negative observation. | Missing, placeholder, or mixed journey identifiers fail the packet. |
| `repository_revision` | One immutable 40-character repository revision shared by every collected proof and negative observation. | Mutable, abbreviated, missing, or mixed revisions fail the packet. |
| `phase_66_1_evidence` | Phase 66.1 evidence id, verifier path, passed result, journey run, and repository revision. | Missing, failed, or unbound clean-host journey evidence fails the packet. |
| `phase_66_2_evidence` | Phase 66.2 evidence id, verifier path, passed result, journey run, and repository revision. | Missing, failed, or unbound Wazuh proof evidence fails the packet. |
| `phase_66_3_evidence` | Phase 66.3 evidence id, verifier path, passed result, journey run, and repository revision. | Missing, failed, or unbound Shuffle proof evidence fails the packet. |
| `phase_66_4_evidence` | Phase 66.4 evidence id, verifier path, passed result, journey run, and repository revision. | Missing, failed, or unbound AI proof evidence fails the packet. |
| `phase_66_5_evidence` | Phase 66.5 evidence id, verifier path, passed result, journey run, and repository revision. | Missing, failed, or unbound report-export proof evidence fails the packet. |
| `phase_66_6_evidence` | Phase 66.6 evidence id, verifier path, passed result, journey run, and repository revision. | Missing, failed, or unbound supportability proof evidence fails the packet. |
| `wazuh_negative_evidence` | Rejected Wazuh source-truth-promotion attempt with authoritative AegisOps record linkage. | Wazuh state cannot become alert, case, evidence, release, or gate truth. |
| `shuffle_negative_evidence` | Rejected Shuffle execution-receipt-promotion attempt with authoritative AegisOps record linkage. | Workflow status cannot bypass approval, action request, receipt, or reconciliation. |
| `ai_negative_evidence` | Rejected AI approval-bypass attempt with authoritative AegisOps record linkage. | AI output cannot approve, execute, reconcile, or close a case. |
| `ticket_negative_evidence` | Rejected ticket case-closure-shortcut attempt with authoritative AegisOps record linkage. | Ticket state remains coordination context only. |
| `evidence_system_negative_evidence` | Rejected external-evidence-truth-promotion attempt with custody and authoritative AegisOps record linkage. | Optional or external evidence cannot become evidence or source truth by itself. |
| `ui_cache_negative_evidence` | Rejected UI-cache workflow-truth-promotion attempt with authoritative AegisOps record linkage. | Browser or UI cache cannot become workflow or gate truth. |
| `demo_data_negative_evidence` | Rejected demo-data release-truth-promotion attempt with authoritative AegisOps record linkage. | Seed or demo data cannot prove live, release, or readiness truth. |
| `report_negative_evidence` | Rejected report gate-truth-promotion attempt with authoritative AegisOps record linkage. | A derived report cannot become workflow, compliance, release, or gate truth. |
| `support_bundle_negative_evidence` | Rejected support-bundle limitation-truth-promotion attempt with authoritative AegisOps record linkage. | A support bundle cannot own support, limitation, restore, release, or gate truth. |
| `release_artifact_negative_evidence` | Rejected release-artifact readiness-truth-promotion attempt with authoritative AegisOps record linkage. | Packaging, integrity, signing, or channel artifacts cannot prove RC or GA readiness. |
| `verifier_output_negative_evidence` | Rejected verifier-output RC-gate-promotion attempt with authoritative AegisOps record linkage. | Verifier output is test evidence, not a release or readiness decision. |
| `issue_lint_output_negative_evidence` | Rejected issue-lint-output RC-gate-promotion attempt with authoritative AegisOps record linkage. | Issue-lint output is planning evidence, not a release or readiness decision. |
| `owner_review` | Accountable reviewer, review timestamp, accepted disposition, and follow-up owner. | Artifact self-approval, rejected review, missing ownership, or stale review fails the packet. |
| `limitation_references` | Reviewed limitation ids, owner, decision timestamp, and follow-up timestamp. | Hidden, unowned, placeholder, or undated limitations fail the packet. |
| `non_claims` | All required RC, GA, production, commercial, parity, and subordinate-truth non-claim labels. | Missing non-claims or positive readiness claims fail the packet. |

A proof packet is fail-closed: once any required field is materialized, every required field must be present, non-placeholder, internally complete, and bound to the same journey run and immutable repository revision.

Materialized proof packets are accepted only as `field=value` assignment lines or Markdown `Field | Value` rows. JSON, YAML, and object-literal evidence syntax is rejected rather than partially interpreted.

## 3. Negative Evidence Matrix

Every negative observation must record `evidence_id`, `surface`, `attempt`, `result=rejected`, `authoritative_record`, `observed_at`, `journey_run_id`, and `repository_revision`.

| Surface | Required rejected attempt | Authoritative fallback |
| --- | --- | --- |
| Wazuh | `source-truth-promotion` | An admitted and linked AegisOps alert, case, or evidence record. |
| Shuffle | `execution-receipt-promotion` | AegisOps approval, action request, execution receipt, and reconciliation records. |
| AI | `approval-bypass` | A reviewed AegisOps recommendation and explicit human decision. |
| Tickets | `case-closure-shortcut` | AegisOps case state and linked audit record. |
| Evidence systems | `external-evidence-truth-promotion` | AegisOps evidence custody, parser, scope, and record linkage. |
| UI cache | `workflow-truth-promotion` | Durable AegisOps workflow and gate records. |
| Demo data | `release-truth-promotion` | Reviewed non-demo release and limitation records. |
| Reports | `gate-truth-promotion` | AegisOps source records plus an explicit gate decision. |
| Support bundle | `limitation-truth-promotion` | AegisOps limitation, restore acceptance, and audit records. |
| Release artifacts | `readiness-truth-promotion` | Reviewed AegisOps release and gate records. |
| Verifier output | `rc-gate-promotion` | An explicit AegisOps RC gate decision. |
| Issue-lint output | `rc-gate-promotion` | An explicit AegisOps RC gate decision. |

Passing one negative observation cannot compensate for a missing surface. Missing, malformed, placeholder-backed, stale, future-dated, mixed-run, mixed-revision, or non-rejected observations fail the whole packet.

## 4. Evidence Binding And Secret Hygiene

Each Phase 66.1-66.6 evidence value must record `evidence_id`, `verifier`, `result=passed`, `journey_run_id`, and `repository_revision`. The verifier path must be the repository-owned focused verifier for that phase slice.

All materialized timestamps must be no more than 24 hours old at verification time and must not be more than five minutes in the future. The owner review and every negative observation must satisfy this freshness window.

The proof pack must not contain production secrets, credentials, authorization material, certificates, key material, raw customer-private data, ticket-private content, customer identifiers, email addresses, or workstation-local paths. Redaction assertions do not permit retaining the forbidden value beside the assertion.

## 5. Authority Boundary

AegisOps records remain authoritative for alert, case, evidence, recommendation, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, restore acceptance, and closeout truth.

Wazuh, Shuffle, AI, tickets, evidence systems, browser state, UI cache, demo data, reports, support bundles, release artifacts, verifier output, issue-lint output, and optional evidence remain subordinate evidence or context only.

The proof pack must reject subordinate-truth promotion, approval bypass, execution bypass, reconciliation bypass, case-closure shortcuts, source-admission shortcuts, inferred RC pass, inferred GA pass, and artifact-driven limitation or closeout decisions.

An accepted owner review records a human disposition; it does not itself grant release authority. Phase 66.8 must evaluate closeout independently against authoritative AegisOps records and accepted limitations.

## 6. Rejection Conditions

The focused verifier rejects:

- missing Phase 66.1-66.6 references, focused verifiers, proof fields, negative surfaces, or README linkage;
- partial, duplicate, cross-section, mixed-run, mixed-revision, stale, future-dated, failed, or placeholder-backed proof packets;
- JSON, YAML, or object-literal evidence syntax that could be silently ignored or ambiguously parsed;
- Wazuh, Shuffle, AI, ticket, evidence-system, UI-cache, demo-data, report, support-bundle, release-artifact, verifier-output, or issue-lint-output truth promotion;
- approval, execution, reconciliation, source-admission, or case-closure bypasses;
- production secrets, credentials, authorization material, certificate or key material, customer-private data, ticket-private data, email addresses, and workstation-local paths;
- RC or GA gate overclaims, production rollout claims, commercial replacement claims, and broad enterprise SIEM/SOAR parity claims.

## 7. Verification

Run `bash scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh`.

Run `bash scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1404 --config <supervisor-config-path>`.

## 8. Non-Goals

Phase 66.7 does not add runtime feature breadth, execute production operations, grant new AI or integration authority, prove real design-partner outcomes, complete production rollout, implement commercial billing or entitlement enforcement, prove Phase 67 GA readiness, or claim broad enterprise SIEM/SOAR parity.

