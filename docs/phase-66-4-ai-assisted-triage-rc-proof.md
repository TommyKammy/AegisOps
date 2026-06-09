# Phase 66.4 AI-Assisted Triage RC Proof

- **Status**: Accepted as the Phase 66.4 AI-assisted triage RC proof contract for release-candidate evidence planning only.
- **Date**: 2026-06-09 Asia/Tokyo
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-66-1-clean-host-rc-e2e-harness.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/phase-59-3-ai-trace-lifecycle-contract.md`, `docs/phase-59-4-ai-disabled-degraded-mode-contract.md`, `docs/phase-60-3-case-timeline-summary-agent.md`, `docs/phase-60-6-cited-recommendation-draft-agent.md`, `docs/phase-63-7-ai-grounding-adapter.md`, `docs/phase-65-closeout-evaluation.md`
- **Related Issues**: #1397, #1401

This contract defines the Phase 66.4 AI-assisted triage RC proof surface. It records how one reviewed AI-assisted triage path produces cited, reviewable summary and recommendation evidence during the Phase 66 RC journey without turning AI output into AegisOps record authority.

The proof depends on the Phase 66.1 clean-host RC E2E harness. It does not replace the clean-host journey, and it does not satisfy the later report export, supportability, authority-boundary proof-pack, closeout, or GA evidence slices.

## 1. Proof Purpose

The AI-assisted triage proof demonstrates that cited assistant output can help an operator review an alert, summarize evidence, mark uncertainty, draft a recommendation, and record accepted, rejected, or unresolved review posture while AegisOps records remain the authoritative system for alert, case, evidence, approval, action, reconciliation, release, gate, and closeout truth.

This proof is RC evidence only. It is not autonomous remediation, AI approval, AI execution, AI reconciliation, AI case closure, detector activation, source-native truth, release truth, gate truth, readiness truth, GA readiness, real design-partner success, broad AI SOC replacement, or commercial replacement readiness.

## 2. AI-Assisted Triage Evidence

Every Phase 66.4 proof packet must include these fields:

| Field | Required evidence | Failure boundary |
| --- | --- | --- |
| `journey_run_id` | The Phase 66.1 run identifier that observed the AI-assisted triage path. | Missing or mismatched run identifiers fail the proof. |
| `repository_revision` | Immutable repository revision for the proof packet. | Mutable branch names fail the proof. |
| `ai_trace_id` | Reviewed AI trace lifecycle record for the cited assistant interaction. | Prompt text, model output, or UI text alone cannot create trace truth. |
| `source_evidence_references` | Reviewed AegisOps evidence ids, alert ids, case ids, and source references used by the assistant. | Missing citations fail the proof. |
| `cited_summary_id` | Cited triage summary linked to exact evidence references and reviewer. | Uncited summaries, invented citations, or hidden source text fail the proof. |
| `uncertainty_flags` | Explicit uncertainty, ambiguity, stale-evidence, and low-confidence flags when present. | Uncertainty cannot be hidden in assistant prose. |
| `recommendation_draft_id` | Draft recommendation with cited rationale, scope, reviewer, and review state. | Recommendation text cannot approve, execute, reconcile, or close records. |
| `operator_review_state` | `accepted`, `rejected`, or `unresolved` with reviewer, timestamp, rationale, and follow-up owner. | Missing review state or AI self-approval fails the proof. |
| `degraded_disabled_posture` | AI disabled, degraded, stale, unavailable, or rejected-output posture and manual fallback path. | AI output cannot be required for RC journey continuation. |
| `prompt_injection_review_id` | Reviewed prompt-injection, instruction-conflict, and unsafe-tool-use assessment. | Prompt-injection compliance or instruction following cannot override AegisOps policy. |
| `limitation_references` | Known limitation ids, owner, decision date, and follow-up date when evidence is incomplete. | Missing limitations cannot be hidden in assistant output. |

## 3. Cited Summary And Reviewability

The proof must cite `docs/phase-59-3-ai-trace-lifecycle-contract.md` and include AI trace evidence for trace id, model family, prompt template, tool context, source evidence references, output hash, reviewer, retention posture, and redaction posture.

The proof must cite `docs/phase-60-3-case-timeline-summary-agent.md` and include cited summary evidence for summary id, alert id, case id, evidence ids, source timestamps, confidence flags, stale-evidence flags, ambiguity flags, reviewer, and review outcome.

The proof must cite `docs/phase-60-6-cited-recommendation-draft-agent.md` and include recommendation draft evidence for draft id, cited rationale, rejected alternatives, unresolved questions, follow-up owner, accepted state, rejected state, and unresolved state.

The proof must cite `docs/phase-59-4-ai-disabled-degraded-mode-contract.md` and include degraded or disabled posture for AI unavailable, AI disabled, stale source evidence, model failure, unsafe output, rejected output, and manual review continuation.

The proof must cite `docs/phase-63-7-ai-grounding-adapter.md` and include grounding evidence that binds assistant output to reviewed AegisOps evidence references. Model output, prompt text, browser state, UI cache, verifier output, issue-lint output, source tool output, and optional evidence remain subordinate evidence.

## 4. Authority Boundary

AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, source admission, and closeout truth.

AI output remains advisory and tool-governed. AI summaries, AI recommendations, AI trace state, model output, prompt text, prompt-injection results, grounding output, tool output, source snippets, citations, confidence scores, uncertainty flags, browser state, UI cache, verifier output, issue-lint output, and optional evidence cannot approve, execute, reconcile, close, release, gate, mutate, or promote AegisOps records.

The proof must reject missing citations, missing review states, missing degraded or disabled posture, missing limitation references, AI approval, AI execution, AI reconciliation, AI case closure, AI-as-truth claims, prompt-injection shortcuts, workstation-local paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, issue-lint-as-readiness-truth, and AI-as-readiness-truth.

## 5. Accepted Limitations

Phase 66.4 records one reviewed AI-assisted triage path for RC evidence. It does not prove autonomous remediation, AI approval, AI execution, AI reconciliation, AI case closure, detector activation, source-native truth, release truth, gate truth, broad AI SOC replacement, real design-partner success, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness.

Later Phase 66 issues must still prove report export, supportability, RC authority-boundary proof pack, and closeout evidence independently.

## 6. Verification

Run `bash scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh`.

Run `bash scripts/test-verify-phase-66-4-ai-assisted-triage-rc-proof.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1401 --config <supervisor-config-path>`.
