# AegisOps Documentation Ownership Map

This document records the default ownership map for major AegisOps documentation areas in one place.

It supplements existing document-control metadata and does not replace per-document owner fields where those fields already exist.

## 1. Purpose

This map makes documentation accountability explicit for the baseline artifacts that govern implementation and operations.

It exists so reviewers can determine, without ambiguity, which team owns each major documentation area before related changes are merged.

This document defines ownership only. It does not change implementation behavior, runtime approval paths, or repository tooling.

## 2. Ownership Terms

Document owner means the team accountable for keeping the document area current, reviewable, and aligned with the approved baseline and accepted ADRs.

For this map, ownership includes maintaining document-control metadata where applicable, reviewing proposed updates for the area, and resolving ambiguity when related artifacts drift out of sync.

If a document inside one of these areas has its own `Owner` or `Owners` field, that field must remain consistent with this map unless an approved update changes the ownership map itself.

## 3. Ownership Map

| Documentation area path | Area | Owner |
| ---- | ---- | ---- |
| `docs/requirements-baseline.md` | Requirements baseline | IT Operations, Information Systems Department |
| `docs/canonical-telemetry-schema-baseline.md` | Canonical telemetry schema baseline | IT Operations, Information Systems Department |
| `docs/source-onboarding-contract.md` | Source onboarding contract baseline | IT Operations, Information Systems Department |
| `docs/sigma-to-opensearch-translation-strategy.md` | Sigma-to-OpenSearch translation strategy baseline | IT Operations, Information Systems Department |
| `docs/detection-lifecycle-and-rule-qa-framework.md` | Detection lifecycle and rule QA framework baseline | IT Operations, Information Systems Department |
| `docs/phase-6-initial-telemetry-slice.md` | Phase 6 initial telemetry family and use-case selection baseline | IT Operations, Information Systems Department |
| `docs/secops-domain-model.md` | SecOps domain model baseline | IT Operations, Information Systems Department |
| `docs/secops-business-hours-operating-model.md` | Business-hours SecOps daily operating model baseline | IT Operations, Information Systems Department |
| `docs/auth-baseline.md` | Authentication, authorization, and service account ownership baseline | IT Operations, Information Systems Department |
| `docs/asset-identity-privilege-context-baseline.md` | Asset, identity, and privilege context baseline | IT Operations, Information Systems Department |
| `docs/response-action-safety-model.md` | Response action safety and approval binding baseline | IT Operations, Information Systems Department |
| `docs/control-plane-state-model.md` | Control-plane state and reconciliation baseline | IT Operations, Information Systems Department |
| `docs/retention-evidence-and-replay-readiness-baseline.md` | Retention, evidence lifecycle, and replay readiness baseline | IT Operations, Information Systems Department |
| `docs/phase-7-ai-hunt-evaluation-baseline.md` | Phase 7 AI hunt evaluation baseline | IT Operations, Information Systems Department |
| `docs/adr/` | Architecture Decision Records (ADRs) | IT Operations, Information Systems Department |
| `docs/parameters/` | Parameter documentation | IT Operations, Information Systems Department |
| `docs/runbook.md` | Runbooks | IT Operations, Information Systems Department |

The requirements baseline owner recorded in `docs/requirements-baseline.md` remains authoritative for that document and is unchanged by this map.

ADR records under `docs/adr/` may identify specific document proposers or reviewers, but repository-level ownership for the ADR area remains assigned to IT Operations, Information Systems Department unless this map is updated explicitly.

The SecOps domain model document remains the shared semantic reference for baseline object definitions and state boundaries and must stay aligned with the approved architecture and requirements baseline.

The business-hours SecOps operating model remains the analyst-workflow reference for triage, case creation, approval timeout handling, after-hours escalation, and handoff expectations under the non-24x7 baseline.

The auth baseline remains the policy reference for operator personas, least-privilege authorization boundaries, machine identity ownership, and secret lifecycle expectations across future monitors, workflows, approvals, and integrations.

The asset, identity, and privilege context baseline remains the Phase 7 design reference for reviewed alias handling, ownership expectations, criticality context, and privilege-relevant entity reasoning without implying live CMDB or IdP authority.

The response action safety model remains the baseline policy reference for action classes, approval binding, idempotency expectations, and post-approval drift protection for future response execution work.

The control-plane state model remains the baseline ownership reference for which records stay in OpenSearch, which stay in n8n, and which require future AegisOps control-plane authority rather than implicit storage inside component-local state.

The retention, evidence lifecycle, and replay readiness baseline remains the policy reference for record-family retention classes, evidence expiration constraints, replay dataset preservation, and restore-readiness assumptions.

The Phase 7 AI hunt evaluation baseline remains the design-review reference for minimum replay corpus coverage, adversarial prompt-injection pressure, citation quality expectations, and trust-blocking failure conditions for future AI-assisted hunt evaluation.

The canonical telemetry schema baseline remains the shared semantic reference for normalized event field expectations and must stay aligned with ECS usage rules, source provenance requirements, and the approved SecOps domain model.

The source onboarding contract baseline remains the shared readiness reference for admitting new telemetry families and must stay aligned with the canonical telemetry schema baseline, provenance expectations, and explicit non-goals for sources that are not yet detection-ready.

The Sigma-to-OpenSearch translation strategy baseline remains the approved boundary for what Sigma content is portable into future OpenSearch detector work, what must be deferred, and when detections must remain OpenSearch-native.

The detection lifecycle and rule QA framework baseline remains the approval-readiness reference for moving reviewed detection content from proposal through activation, deprecation, and retirement without bypassing staging or evidence expectations.

The Phase 6 initial telemetry slice document remains the narrow scoping reference for the first validated family and use-case set and must stay aligned with the business-hours operating model, replay-readiness assumptions, and Sigma translation boundaries.

Parameter documents under `docs/parameters/` remain the authoritative human-readable home for parameter references, category explanations, ownership notes, and review guidance.

Runbooks remain owned as controlled operator documentation and must stay consistent with the approved operating model, approval constraints, and validation expectations defined elsewhere in the repository.
