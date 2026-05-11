# Phase 59.3 AI Trace Lifecycle Contract

- **Status**: Accepted lifecycle contract slice
- **Date**: 2026-05-11
- **Owner**: AegisOps maintainers
- **Related Issues**: #1252, #1255

This contract defines the AI trace lifecycle states for created, reviewed, accepted, corrected, rejected, and expired traces before Phase 59 expands disabled or degraded mode, prompt fixtures, stale or conflicting evidence fixtures, trace queue UI/API implementation, closeout work, or Phase 60 daily AI operations.

It is limited to the Phase 59.3 AI trace lifecycle contract. It does not implement new model routing, provider selection, tool execution, trace queue behavior, disabled-mode behavior, daily AI operations, approval, execution, reconciliation, case closure, detector activation, source truth, production write authority, or commercial-readiness claims.

## 1. Required Lifecycle Fields

Every AI trace lifecycle state must require registered agent linkage, registered tool linkage, citations, reviewed record family and identifier linkage, expiration handling, and advisory-only authority.

The executable lifecycle artifact lives in `docs/automation/ai-trace-lifecycle.json`.

The lifecycle artifact is a repo-owned policy artifact. It is not runtime truth, workflow truth, approval truth, execution truth, reconciliation truth, release truth, gate truth, closeout truth, or source truth.

## 2. Authority Boundary

AI remains advisory, registered, audited, cited, and subordinate to reviewed AegisOps records.

No AI trace lifecycle state or transition may grant approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, or authority-widening capability.

Accepted and corrected AI trace states mean only that an operator reviewed the trace as advisory context. They do not close cases, approve actions, execute actions, reconcile receipts, activate detectors, create source truth, or promote trace output over the reviewed AegisOps record chain.

Rejected and expired AI trace states must preserve auditability while keeping the trace unusable as accepted advisory context until a new cited trace is created and reviewed.

This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.

## 3. Lifecycle States

| State | Meaning | Authority ceiling |
| --- | --- | --- |
| `created` | Trace was produced by a registered agent through registered tools against a directly linked reviewed record and citations. | Advisory only, subordinate to AegisOps records. |
| `reviewed` | Operator review has inspected the trace, citations, linkage, freshness, and unresolved questions. | Advisory only, subordinate to AegisOps records. |
| `accepted` | Operator accepted the trace as advisory context for the reviewed record. | Advisory only, subordinate to AegisOps records. |
| `corrected` | Operator corrected the trace while preserving reviewer/action metadata and citations. | Advisory only, subordinate to AegisOps records. |
| `rejected` | Operator rejected the trace as unusable advisory context. | Advisory only, subordinate to AegisOps records. |
| `expired` | Trace passed its expiration boundary and cannot be accepted without a new cited trace lifecycle. | Advisory only, subordinate to AegisOps records. |

These names identify trace review states, not workflow states with independent authority.

## 4. Transition Rules

Allowed transitions are limited to:

- `created` to `reviewed`;
- `created` to `expired`;
- `reviewed` to `accepted`;
- `reviewed` to `corrected`;
- `reviewed` to `rejected`;
- `reviewed` to `expired`;
- `accepted` to `expired`;
- `corrected` to `expired`.

Review outcome transitions must include reviewer/action metadata. Expiration transitions must include expiration metadata. No transition may mutate alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, closeout, detector, or source-truth records.

## 5. Trace Review Queue Skeleton

The Phase 59.3 contract only reserves the trace review queue inputs needed by Phase 59.7: `trace_id`, `state`, `reviewed_record_family`, `reviewed_record_id`, `registered_agent_name`, `registered_tool_names`, `citation_ids`, `expires_at`, and `review_required`.

The queue skeleton is not a production UI/API implementation and must not treat queue ordering, badge text, cache state, browser state, or trace state as workflow truth.

## 6. Verifier Requirements

The lifecycle verifier must fail when:

- the contract doc is missing;
- the lifecycle artifact is missing or invalid JSON;
- any lifecycle state is missing created, reviewed, accepted, corrected, rejected, or expired coverage;
- any lifecycle state omits registered agent linkage, registered tool linkage, citation linkage, reviewed record family and identifier linkage, or expiration handling;
- any lifecycle state references an unregistered agent or tool;
- review outcome states omit reviewer/action metadata requirements;
- allowed transitions omit required lifecycle paths or allow expired traces to become accepted without a new trace;
- any lifecycle state or transition grants approval, execution, reconciliation, case closure, detector activation, source-truth creation, production write, policy bypass, workflow truth, or authority widening;
- publishable artifacts contain workstation-local absolute paths.

## 7. Validation

Run `bash scripts/verify-phase-59-3-ai-trace-lifecycle-contract.sh`.

Run `bash scripts/test-verify-phase-59-3-ai-trace-lifecycle-contract.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1255 --config <supervisor-config-path>`.

## 8. Non-Goals

- No new production write authority is introduced.
- No AI output, trace state, citation, registry row, lifecycle artifact, verifier output, issue-lint output, browser state, UI state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, or prompt text becomes authoritative workflow truth.
- No Phase 59.7 trace review queue UI/API implementation is introduced.
- No Phase 60 daily AI operations behavior is implemented.
- No model/provider selection, billing, prompt marketplace, tool marketplace, or agent ecosystem breadth is implemented.
- No approval, execution, reconciliation, case closure, detector activation, source-truth creation, production write, or policy bypass is delegated to AI.
