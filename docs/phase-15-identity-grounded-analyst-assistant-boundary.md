# AegisOps Phase 15 Identity-Grounded Analyst-Assistant Boundary

## 1. Purpose

This document defines the approved advisory-only analyst-assistant boundary for Phase 15.

It supplements `docs/control-plane-state-model.md`, `docs/control-plane-runtime-service-boundary.md`, `docs/asset-identity-privilege-context-baseline.md`, `docs/phase-14-identity-rich-source-family-design.md`, `docs/phase-13-guarded-automation-ci-validation.md`, `docs/response-action-safety-model.md`, and `docs/adr/0002-wazuh-shuffle-control-plane-thesis.md` by defining how the assistant may ground reasoning in reviewed control-plane records, reviewed context, and linked evidence.

The operator-facing companion guidance lives in `docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md`.

This document defines review scope only. It does not approve live assistant execution, approval automation, reconciliation authority, UI work, or substrate-side implementation.

## 2. First-Class Grounding Inputs

The assistant may treat the following reviewed control-plane record families as first-class grounding inputs:

| Record family | Grounding use |
| ---- | ---- |
| `Alert` | Primary triage record for current state, review status, linked evidence, and analyst disposition. |
| `Case` | Primary investigation record for ownership, scope, case lifecycle, and reviewed context. |
| `Evidence` | Primary custody record for linked artifacts, provenance, and evidence-backed claims. |
| `Recommendation` | Primary record for proposed next steps, rationale, and review state. |
| `Reconciliation` | Primary record for mismatch state, linkage paths, and authoritative comparison of control-plane truth with observed outcomes. |
| `Approval Decision` | Primary record for whether a specific request was approved, rejected, expired, canceled, or superseded. |
| `Action Request` | Primary record for the requested intent, target scope, payload binding, and review window. |
| `Action Execution` | Primary record for approved-versus-actual execution outcome and correlated execution evidence. |
| `Observation` | Primary record for analyst-asserted facts tied to evidence or scoped investigative work. |
| `Lead` | Primary record for triage hypotheses or follow-up directions under review. |
| `Hunt` and `Hunt Run` | Primary record for bounded investigative context and run history when explicitly linked to reviewed evidence. |
| `AI Trace` | Primary record for model output, reviewer context, and acceptance or rejection history. |
| `Analytic Signal` | Supporting record for upstream linkage when it is already attached to an alert, case, or evidence set. |

The assistant may treat the following linkage paths as first-class grounding paths:

- `alert -> evidence`
- `case -> evidence`
- `alert -> case`
- `recommendation -> alert or case`
- `reconciliation -> alert, case, approval decision, action request, or action execution`
- `ai trace -> recommendation or case`
- `hunt or hunt run -> observation, lead, recommendation, or case`

Reviewed context fields on those records are also first-class grounding inputs when they preserve stable identifiers, reviewed provenance, and explicit linkage.

The assistant must prefer the reviewed control-plane record and its linked evidence over any substrate-local raw path, analytics cache entry, or summary row that merely restates the same event.

## 3. Reviewed Context Inputs

The assistant may ground on the following reviewed context fields when they are present on reviewed control-plane records:

| Field group | Minimum expectation |
| ---- | ---- |
| Stable identifiers | `alert_id`, `case_id`, `evidence_id`, `recommendation_id`, `reconciliation_id`, `approval_decision_id`, `action_request_id`, `action_execution_id`, `hunt_id`, `hunt_run_id`, `ai_trace_id`, `analytic_signal_id`, and `substrate_detection_record_id` remain the preferred identifiers for comparison and linking. |
| Reviewed provenance | Source family, source record id, operation name, payload hash, correlation id, execution surface id, and review timestamp remain explicit when they exist. |
| Identity context | Actor, owner, target, privilege scope, account type, and accountable source identity remain explicit when a reviewed record already carries them. |
| Review state | Lifecycle state, review state, disposition, and mismatch state remain explicit rather than inferred from logs or summaries. |
| Evidence context | Linked evidence ids, evidence provenance, and evidence relationship type remain explicit rather than reconstructed from text snippets. |

Substrate-local raw paths, cache keys, and non-reviewed summaries may be consulted only as supporting pointers when they are already referenced by a reviewed control-plane record.

They are not authoritative grounding inputs on their own.

## 4. Optional OpenSearch Analytics Extension

OpenSearch may contribute optional analytics or evidence lookups to the assistant path after the reviewed control-plane grounding path exists.

It is a secondary analyst-assistant extension only: it may enrich reviewed assistance with corroborating analytics, but it must not become a prerequisite for assistance or a replacement for reviewed control-plane grounding.

OpenSearch does not own alert, case, recommendation, approval, action, or reconciliation truth.

Any OpenSearch-derived enrichment must stay secondary to reviewed control-plane records and linked evidence, and it must not overwrite or outrank reviewed control-plane truth.

If OpenSearch is absent, stale, incomplete, or conflicting, the assistant must fall back to control-plane-only grounding and preserve the discrepancy for review rather than treating the OpenSearch result as authoritative.

This safe fallback preserves reviewed grounding instead of promoting OpenSearch-derived analytics into authority.

This keeps the boundary narrow enough to support optional enrichment without reviving an analytics-first product thesis.

## 5. Cited Advisory-Output Contract

The reviewed output layer for Phase 15.1 must render from assistant-context snapshots rather than from free-form assistant text.

The contract is a narrow structured advisory-output contract for a cited triage summary, case summary, or next-step recommendation draft.

Each rendered advisory output must expose the following fields:

| Contract field | Minimum contract rule |
| ---- | ---- |
| `cited summary` | A concise advisory summary that cites the reviewed records, linked evidence, or reviewed context identifiers supporting each material claim. |
| `key observations` | A bounded list of materially relevant observations tied to reviewed records, linked evidence, or reviewed context identifiers. |
| `unresolved questions` | A bounded list of open gaps, conflicts, or missing evidence that keep the output advisory and incomplete. |
| `candidate recommendations` | Draft next steps only, explicitly framed as proposals rather than approvals, execution instructions, or reconciliation truth. |
| `citations` | The explicit record ids, evidence ids, reviewed context identifiers, or reviewed linkage references that anchor every material claim. |
| `uncertainty flags` | Explicit markers for missing citations, conflicting reviewed context, unresolved identity ambiguity, stale enrichment, or other reasons the output must remain tentative. |

Every material claim in the contract must anchor to reviewed control-plane records, linked evidence, or reviewed context identifiers.

The contract must preserve the cited linkage between the assistant-context snapshots and the rendered output so a reviewer can trace each claim back to reviewed inputs.

The contract keeps the assistant advisory-only and does not allow the output layer to imply approval, execution, or reconciliation authority.

## 6. Fail-Closed Rendering Rules

The cited advisory-output contract must fail-closed.

If citations are missing, the contract must not render a supported claim and must remain unresolved.

If reviewed context is conflicting, the contract must surface the conflict in unresolved questions and uncertainty flags rather than silently choosing a side.

If identity ambiguity cannot be resolved from stable identifiers and reviewed linkage, the contract must not render the entities as the same actor, asset, or accountable subject and must remain unresolved.

If optional enrichment is stale, incomplete, or contradictory, the contract must cite the reviewed control-plane state first and preserve the discrepancy as uncertainty rather than normalizing the enrichment into truth.

## 7. Identity Ambiguity and Alias Handling

The assistant must fail closed when only alias-style source metadata or otherwise non-stable metadata is available.

Alias-style metadata includes display names, short names, path fragments, heuristic name matches, or other source-local labels that do not carry a stable identifier.

The assistant must not assert equality when the only available evidence is alias-style metadata.

The assistant may describe a relationship as possible, reviewed, or unresolved only when a reviewed control-plane record or reviewed context field explicitly supplies that relationship.

When stable identifiers differ, the assistant must treat the records as distinct until a reviewed reconciliation record or reviewed alias mapping says otherwise.

The assistant must not invent transitive identity stitching across systems, and it must not infer ownership transfer, privilege transfer, or actor equivalence from naming similarity alone.

If identity ambiguity remains, the assistant must report that ambiguity directly instead of collapsing the records into a single entity.

## 8. Advisory-Only Boundary

The assistant is advisory-only.

It may summarize reviewed records, compare reviewed evidence, explain reviewed mismatch state, and draft candidate next steps.

It must not approve actions, execute actions, mutate authoritative records, or present its own output as reconciliation truth.

It must not treat substrate-local summaries or analytics caches as superior to reviewed control-plane records when those records disagree.

It must not become the authority for approval, execution, or reconciliation state.

If the assistant is asked for a decision, the answer must point back to the reviewed control-plane records and their explicit review state rather than pretending to produce new authority.

## 9. Safe Query, Citation, and Prompt-Pressure Constraints

The assistant must use the Safe Query Gateway policy for any read-oriented internal lookup that would otherwise rely on free-form search, query expansion, or tool selection outside reviewed control-plane paths.

Prompt content, analyst notes, and optional-extension instructions are untrusted input.

The assistant must not use prompt content, analyst text, or optional-extension shortcuts to bypass validation, widen scope, or acquire approval or execution authority.

The assistant must preserve citation completeness for every advisory claim.

If a claim cannot be tied back to reviewed records or cited observations, the response must stay advisory-only and unresolved rather than silently widening the answer.

Optional extension inputs, including OpenSearch analytics, do not override reviewed control-plane truth, stable identifiers, or the citation requirement.

Alias-style fields may suggest a match, but when stable identifiers differ the assistant must keep the records distinct and report the ambiguity instead of normalizing them into one actor or asset.

## 10. Explicit Non-Goals

This document does not approve live assistant orchestration, prompt execution, or tool wiring.

This document does not approve a UI, a background agent, a new execution substrate, or any direct substrate-local action path.

This document does not redefine the Phase 13 approval and execution boundary or the Phase 14 reviewed-context expansion boundary.

This document does not authorize the assistant to synthesize new identity truth from source-local labels, cache rows, or summary artifacts.

This document does not approve live provider orchestration, free-form backend query expansion, or optional OpenSearch runtime enrichment as a requirement for the output contract.

## 11. Baseline Alignment Notes

This boundary remains aligned with `docs/control-plane-state-model.md` by treating alerts, cases, evidence, recommendations, reconciliations, approval decisions, action requests, and action executions as authoritative control-plane records.

It remains aligned with `docs/control-plane-runtime-service-boundary.md` by keeping the assistant downstream of the live control-plane boundary rather than turning it into the control plane itself.

It remains aligned with `docs/asset-identity-privilege-context-baseline.md` and `docs/phase-14-identity-rich-source-family-design.md` by preserving reviewed identity and privilege context without collapsing identity ambiguity into guessed equality.

It remains aligned with `docs/safe-query-gateway-and-tool-policy.md` and `docs/phase-7-ai-hunt-design-validation.md` by keeping prompt-driven query expansion, citation-bearing response shaping, and prompt-injection handling inside the reviewed safe-query boundary.

It remains aligned with the Phase 10 and Phase 15 thesis pivots by keeping OpenSearch as an optional enrichment substrate rather than an authoritative truth boundary.

It remains aligned with `docs/phase-13-guarded-automation-ci-validation.md`, `docs/response-action-safety-model.md`, and `docs/adr/0002-wazuh-shuffle-control-plane-thesis.md` by keeping AI advisory-only and separating reviewed decision support from approval and execution authority.
