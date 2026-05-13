# Phase 60.3 Case Timeline Summary Agent

- **Status**: Implemented focused Phase 60 slice
- **Date**: 2026-05-13
- **Owner**: AegisOps maintainers
- **Related Issues**: #1269, #1272

This contract defines the bounded case timeline summary agent for Phase 60 daily operations. It summarizes reviewed case timeline chains with citations, authority labels, and uncertainty flags without changing case state, segment state, approval state, execution state, reconciliation state, subordinate evidence posture, or workflow routing.

The runtime entry point is `aegisops.control_plane.assistant.case_timeline_summary.build_case_timeline_summary`.

## Authority Boundary

The case timeline summary agent is read-only, cited, registered-tool-backed, reviewable, and subordinate to reviewed AegisOps records.

The agent may summarize reviewed case timeline segments, cite directly linked case, alert, evidence, recommendation, action request, approval, execution receipt, reconciliation, source-health, AI trace, and explicit timeline-gap context.

The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, complete timeline segments, suppress uncertainty, hide citations, resolve conflicts, or treat summary output as workflow truth.

## Registered Tool Linkage

The agent uses the Phase 60.3 `case_timeline_summary` tool registration in `docs/automation/ai-tool-registry.json`.

Every summary output must cite:

- the reviewed case anchor `case:<id>`;
- directly linked `alert:<id>`, `evidence:<id>`, `recommendation:<id>`, `action_request:<id>`, `approval_decision:<id>`, `action_execution:<id>`, `reconciliation:<id>`, `source_health:<id>`, or `ai_trace:<id>` records when present;
- explicit `timeline_gap:<segment>` citations when a reviewed segment is missing but operator-visible;
- `docs/automation/ai-agent-registry.json`;
- `docs/automation/ai-tool-registry.json`;
- `docs/automation/ai-disabled-degraded-mode-contract.json`.

## Disabled And Degraded Behavior

If AI advisory posture is disabled or degraded, the agent returns bounded fallback output. It keeps the non-AI case workflow available from authoritative case records, does not create AI traces, and does not generate summary segments.

If timeline evidence is missing, malformed, uncited, cache-sourced, unsupported, or contract-mismatched, the agent fails closed with explicit unresolved reasons rather than inventing a summary.

Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress uncertainty, complete timeline segments, or resolve conflicts must be blocked.

## Operator UI

The operator UI may render `case_timeline_summary` only as advisory review context. The data-provider contract rejects summary payloads that are not read-only, are not advisory-only, can create trace truth, omit citations, or claim that display context can complete workflow state.

## Validation

Run `python3 -m unittest control-plane.tests.test_phase60_3_case_timeline_summary_agent`.

Run `npm --prefix apps/operator-ui test -- OperatorRoutes.test.tsx`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1272 --config <supervisor-config-path>`.

## Non-Goals

- No autonomous approval, execution, reconciliation, case closure, detector activation, source-truth creation, timeline completion, policy bypass, or production write authority is introduced.
- No AI output, summary output, registry row, verifier output, issue-lint output, UI state, browser state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, prompt text, or model output becomes authoritative workflow truth.
- No Phase 61 SIEM breadth, Phase 62 SOAR breadth, Phase 66 RC proof, Beta, RC, GA, commercial replacement readiness, model marketplace, provider marketplace, prompt marketplace, tool marketplace, or customer-private prompt/data handling is implemented.
