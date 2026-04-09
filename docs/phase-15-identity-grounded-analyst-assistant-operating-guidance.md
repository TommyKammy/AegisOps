# AegisOps Phase 15 Identity-Grounded Analyst-Assistant Operating Guidance

## 1. Purpose

This document gives operators the reviewed operating guidance for the Phase 15 analyst assistant.

It is the operator-facing companion to `docs/phase-15-identity-grounded-analyst-assistant-boundary.md` and the validation record in `docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md`.

This guidance stays within the approved advisory-only boundary. It does not authorize live orchestration, approval automation, reconciliation authority, user-interface changes, or substrate-side rollout procedures.

## 2. Grounding Order

When the assistant is used for analyst support, operators should expect it to ground its response in reviewed control-plane records first.

The reviewed grounding order is:

1. reviewed control-plane records and their explicit review state;
2. linked evidence attached to those records;
3. reviewed context fields that preserve stable identifiers, provenance, identity context, review state, and evidence context; and
4. only then, secondary enrichment that corroborates the reviewed record set.

The assistant should be able to explain which reviewed records support a claim using record identifiers, evidence identifiers, or other stable references from the control plane.

The assistant should prefer the reviewed record over any substrate-local summary, cache row, or analytics extract that merely restates the same event.

## 3. Reviewed Records To Trust First

Operators should treat the following reviewed control-plane record families as the primary grounding set:

- `Alert`
- `Case`
- `Evidence`
- `Recommendation`
- `Reconciliation`
- `Approval Decision`
- `Action Request`
- `Action Execution`
- `Observation`
- `Lead`
- `Hunt` and `Hunt Run`
- `AI Trace`
- `Analytic Signal` when it is already attached to a reviewed alert, case, or evidence set

The assistant should not treat an unreviewed substrate-local row, a search hit, or a system-generated summary as equivalent to those reviewed records.

## 4. Uncertainty Handling

Operators must preserve uncertainty whenever the assistant only has alias-style metadata, heuristic name matches, or other non-stable source labels.

Alias-style metadata includes display names, short names, path fragments, or other local labels that do not prove stable identity.

If stable identifiers differ, the assistant should keep the records distinct until a reviewed reconciliation record or reviewed alias mapping resolves the relationship.

If the answer depends on missing evidence, conflicting provenance, or incomplete reviewed context, the assistant should say that the result is unresolved instead of collapsing the gap into certainty.

The assistant must not invent ownership transfer, actor equivalence, or privilege transfer from naming similarity alone.

## 5. Citation Expectations

Every advisory claim should be tied back to reviewed records or linked evidence.

If a claim cannot be cited from the reviewed record set, the operator should treat the answer as advisory only and incomplete.

Operators should expect citations to point back to the record family, stable identifier, review state, or evidence linkage that supports the claim.

If citations are missing, stale, or internally inconsistent, the assistant output should be reviewed as an unresolved draft rather than promoted to operational truth.

## 6. Advisory Output Review Contract

Operators should expect the reviewed output layer to render from assistant-context snapshots rather than from free-form assistant text.

The reviewed advisory output should stay inside a narrow structured advisory-output contract for a cited triage summary, case summary, or next-step recommendation draft.

Each rendered output should include a cited summary, key observations, unresolved questions, candidate recommendations, citations, and uncertainty flags.

Every material claim should anchor to reviewed control-plane records, linked evidence, or reviewed context identifiers so the operator can trace it back to the reviewed snapshot.

If citations are missing, reviewed context is conflicting, or identity ambiguity cannot be resolved from stable identifiers and reviewed linkage, the output should fail-closed and remain unresolved.

This output contract must stay advisory-only and must not allow the output layer to imply approval, execution, or reconciliation authority.

## 7. Optional OpenSearch Enrichment

OpenSearch may be used as a secondary OpenSearch enrichment source after the reviewed control-plane path already exists.

It may help corroborate a reviewed record or provide additional evidence lookup context, but it is not authoritative.

OpenSearch must never outrank reviewed control-plane truth, and it does not own alert, case, recommendation, approval, action, or reconciliation state.

If OpenSearch is absent, stale, incomplete, or conflicting, the assistant should fall back to control-plane-only grounding and preserve the discrepancy for review.

Operators should treat any OpenSearch-derived result as secondary enrichment that needs reviewed confirmation before it is relied on.

## 8. Advisory-Only Boundary

The assistant is advisory-only.

It may summarize reviewed records, compare reviewed evidence, explain reviewed mismatch state, and draft candidate next steps.

It must not approve actions, execute actions, mutate authoritative records, or present its own output as reconciliation truth.

If an operator asks the assistant for a decision, the answer should point back to the reviewed control-plane records and their explicit review state instead of pretending to create new authority.

## 9. Safe Lookup Practice

When a read-oriented internal lookup is needed, operators should expect the assistant to use the Safe Query Gateway policy rather than free-form search or prompt-shaped ad hoc expansion.

Prompt text, analyst notes, and optional-extension hints are untrusted input. They must not be used to bypass validation, widen scope, or obtain approval or execution authority.

The operating rule is simple: query reviewed paths first, preserve citations, and do not let prompt pressure rewrite the trust boundary.

## 10. Operator Checklist

Use this checklist when reviewing assistant output:

1. Confirm the answer cites reviewed control-plane records or linked evidence.
2. Confirm the answer preserves ambiguity when identifiers or provenance are not stable.
3. Confirm any OpenSearch enrichment is treated as corroboration only.
4. Confirm the answer does not claim approval, execution, or reconciliation authority.
5. Confirm missing evidence is called out as unresolved instead of being guessed.
6. Confirm cited triage summaries, case summaries, and recommendation drafts render from assistant-context snapshots using the reviewed contract fields.

## 11. Non-Goals

This guidance does not define live rollout procedure, marketing language, or environment-specific commands.

It does not replace the Phase 15 boundary document, the Safe Query Gateway policy, the control-plane state model, or the response-action safety model.

It does not authorize direct substrate changes or any bypass around reviewed control-plane records.

It does not authorize live provider orchestration, free-form backend query expansion, or optional OpenSearch runtime enrichment as part of the output contract.

## 12. Baseline Alignment

This guidance remains aligned with `docs/phase-15-identity-grounded-analyst-assistant-boundary.md` by keeping the assistant advisory-only and grounded in reviewed control-plane records and linked evidence.

It remains aligned with `docs/safe-query-gateway-and-tool-policy.md` by keeping read-oriented internal lookup inside the reviewed safe-query path.

It remains aligned with `docs/control-plane-state-model.md` and `docs/control-plane-runtime-service-boundary.md` by keeping control-plane records authoritative and by treating OpenSearch as optional enrichment rather than a truth source.

It remains aligned with `docs/asset-identity-privilege-context-baseline.md` and `docs/phase-14-identity-rich-source-family-design.md` by preserving reviewed identity and privilege context without collapsing alias-style metadata into certainty.

It remains aligned with `docs/phase-13-guarded-automation-ci-validation.md`, `docs/response-action-safety-model.md`, and `docs/adr/0002-wazuh-shuffle-control-plane-thesis.md` by keeping AI support below approval and execution authority.
