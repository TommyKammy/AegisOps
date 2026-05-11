# Phase 59.2 Tool Registry Contract

- **Status**: Accepted registry contract slice
- **Date**: 2026-05-11
- **Owner**: AegisOps maintainers
- **Related Issues**: #1252, #1254

This contract defines the required registry fields for every AegisOps AI tool before Phase 59 expands trace lifecycle, disabled or degraded mode, prompt fixtures, stale or conflicting evidence fixtures, trace queue, closeout work, or Phase 60 daily AI operations.

It is limited to the Phase 59.2 tool registry contract. It does not implement new model routing, provider selection, tool execution, trace queue behavior, disabled-mode behavior, daily AI operations, approval, execution, reconciliation, case closure, detector activation, source truth, production write authority, or commercial-readiness claims.

## 1. Required Registry Fields

Every tool registry row must include tool name, purpose, allowed record families, required citations, audit fields, disallowed authority, and authority ceiling.

The executable registry lives in `docs/automation/ai-tool-registry.json`.

The registry is a repo-owned policy artifact. It is not runtime truth, workflow truth, approval truth, execution truth, reconciliation truth, release truth, gate truth, closeout truth, or source truth.

## 2. Authority Boundary

AI remains advisory, registered, audited, cited, and subordinate to reviewed AegisOps records.

No tool registry row may grant approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, or authority-widening capability.

Registered tools may query reviewed records, look up evidence, look up source health, look up runbooks, draft recommendations, draft action requests, and explain doctor findings only when the output is cited, audited, and subordinate to explicit AegisOps records.

This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.

## 3. Registered Tools

The initial registry covers the AI tool surfaces needed by the Phase 59 governance foundation:

| Tool | Purpose | Authority ceiling |
| --- | --- | --- |
| `safe_query` | Read-only scoped query planning and retrieval against reviewed records. | Advisory only, subordinate to AegisOps records. |
| `evidence_lookup` | Retrieve directly linked reviewed evidence or explicit evidence gaps. | Advisory only, subordinate to AegisOps records. |
| `source_health_lookup` | Retrieve source-health context from directly linked backend records. | Advisory only, subordinate to AegisOps records. |
| `runbook_lookup` | Retrieve reviewed runbook and operating guidance references. | Advisory only, subordinate to AegisOps records. |
| `recommendation_draft` | Draft reviewable recommendation text from cited context. | Advisory only, subordinate to AegisOps records. |
| `action_request_draft` | Draft reviewable action-request text without approval or dispatch. | Advisory only, subordinate to AegisOps records. |
| `doctor_explanation` | Explain supportability and doctor findings from cited records and checks. | Advisory only, subordinate to AegisOps records. |

These names identify contract rows, not autonomous tools with independent authority.

## 4. Verifier Requirements

The registry verifier must fail when:

- the contract doc is missing;
- the registry artifact is missing or invalid JSON;
- any tool registry row is missing tool name, purpose, allowed record families, required citations, audit fields, disallowed authority, or authority ceiling;
- any tool registry row grants approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, or authority-widening capability;
- any tool registry row omits citation requirements for `record_family`, `record_id`, or `evidence_reference`;
- any tool registry row omits audit fields for `tool_name`, `agent_name`, `trace_id`, `requested_by`, `record_family`, `record_id`, `citation_ids`, `decision`, or `timestamp`;
- any tool registry row omits disallowed approval, execution, reconciliation, case closure, detector activation, source-truth creation, production write, or policy-bypass authority;
- any registry artifact contains an unregistered tool for this slice;
- publishable artifacts contain workstation-local absolute paths.

## 5. Validation

Run `bash scripts/verify-phase-59-2-tool-registry-contract.sh`.

Run `bash scripts/test-verify-phase-59-2-tool-registry-contract.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1254 --config <supervisor-config-path>`.

## 6. Non-Goals

- No new production write authority is introduced.
- No AI output, trace state, citation, registry row, verifier output, issue-lint output, browser state, UI state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, or prompt text becomes authoritative workflow truth.
- No Phase 60 daily AI operations behavior is implemented.
- No model/provider selection, billing, prompt marketplace, tool marketplace, or agent ecosystem breadth is implemented.
- No approval, execution, reconciliation, case closure, detector activation, source-truth creation, production write, or policy bypass is delegated to AI.
