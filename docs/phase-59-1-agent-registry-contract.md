# Phase 59.1 Agent Registry Contract

- **Status**: Accepted registry contract slice
- **Date**: 2026-05-11
- **Owner**: AegisOps maintainers
- **Related Issues**: #1252, #1253

This contract defines the required registry fields for every AegisOps AI agent before Phase 59 expands tool registry, trace lifecycle, disabled or degraded mode, prompt fixtures, stale or conflicting evidence fixtures, trace queue, or closeout work.

It is limited to the Phase 59.1 registry contract. It does not implement new model routing, provider selection, tool execution, trace queue behavior, disabled-mode behavior, daily AI operations, approval, execution, reconciliation, case closure, detector activation, source truth, production write authority, or commercial-readiness claims.

## 1. Required Registry Fields

Every registry row must include agent name, purpose, allowed tools, disallowed tools, record families, citation requirements, and authority ceiling.

The executable registry lives in `docs/automation/ai-agent-registry.json`.

The registry is a repo-owned policy artifact. It is not runtime truth, workflow truth, approval truth, execution truth, reconciliation truth, release truth, gate truth, or source truth.

## 2. Authority Boundary

AI remains advisory, registered, audited, cited, and subordinate to reviewed AegisOps records.

No agent registry row may grant approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, or authority-widening capability.

Allowed tools are limited to read-only inspection, cited context assembly, advisory summary drafting, evidence-gap identification, safe next-step drafting, and reviewable action-request draft preparation inside existing reviewed AegisOps record boundaries.

Disallowed tools must explicitly include approval, execution, reconciliation, case closure, detector activation, source-truth creation, and policy bypass.

This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.

## 3. Registered Agents

The initial registry covers the AI surfaces already present in the reviewed product path:

| Agent | Purpose | Authority ceiling |
| --- | --- | --- |
| `analyst_assistant_context_agent` | Assemble cited context for one reviewed control-plane record. | Advisory only, subordinate to AegisOps records. |
| `live_assistant_summary_agent` | Draft a bounded cited summary from reviewed context. | Advisory only, subordinate to AegisOps records. |
| `advisory_action_request_drafting_agent` | Prepare reviewable action-request draft text from cited advisory context. | Advisory only, subordinate to AegisOps records. |
| `today_focus_advisory_agent` | Suggest focus lanes for daily workbench projection from directly linked backend records. | Advisory only, subordinate to AegisOps records. |

These names identify contract rows, not autonomous actors with independent authority.

## 4. Verifier Requirements

The registry verifier must fail when:

- the contract doc is missing;
- the registry artifact is missing or invalid JSON;
- any registry row is missing agent name, purpose, allowed tools, disallowed tools, record families, citation requirements, or authority ceiling;
- any registry row grants approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, or authority-widening capability;
- any registry row omits citation requirements for `record_family`, `record_id`, or `evidence_reference`;
- any registry row omits disallowed approval, execution, reconciliation, case closure, detector activation, source-truth creation, or policy-bypass tools;
- publishable artifacts contain workstation-local absolute paths.

## 5. Validation

Run `bash scripts/verify-phase-59-1-agent-registry-contract.sh`.

Run `bash scripts/test-verify-phase-59-1-agent-registry-contract.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1253 --config <supervisor-config-path>`.

## 6. Non-Goals

- No new production write authority is introduced.
- No AI output, trace state, citation, registry row, verifier output, issue-lint output, browser state, UI state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, or prompt text becomes authoritative workflow truth.
- No Phase 60 daily AI operations behavior is implemented.
- No model/provider selection, billing, prompt marketplace, tool marketplace, or agent ecosystem breadth is implemented.
- No approval, execution, reconciliation, case closure, detector activation, source-truth creation, or policy bypass is delegated to AI.
