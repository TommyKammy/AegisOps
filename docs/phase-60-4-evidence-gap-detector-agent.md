# Phase 60.4 Evidence Gap Detector Agent

- **Status**: Implemented focused Phase 60 slice
- **Date**: 2026-05-13
- **Owner**: AegisOps maintainers
- **Related Issues**: #1269, #1273

This contract defines the bounded evidence gap detector agent for Phase 60 daily operations. It identifies missing identity owner, stale source health, receipt present but reconciliation missing, evidence conflict, and missing citation gaps from directly linked reviewed AegisOps records without changing source health, receipt state, reconciliation state, evidence truth, case truth, approval state, execution state, or workflow routing.

The runtime entry point is `aegisops.control_plane.assistant.evidence_gap_detector.build_evidence_gap_detector`.

## Authority Boundary

The evidence gap detector agent is read-only, cited, registered-tool-backed, reviewable, and subordinate to reviewed AegisOps records.

The agent may identify evidence gaps, cite directly linked case, alert, evidence, recommendation, action request, approval, execution receipt, reconciliation, source-health, AI trace, and explicit gap context, and suggest safe next review steps.

The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, create evidence truth, select truth between conflicting records, suppress uncertainty, hide citations, or treat detector output as workflow truth.

## Registered Tool Linkage

The agent uses the Phase 60.4 `evidence_gap_detector` tool registration in `docs/automation/ai-tool-registry.json`.

Every detector output must cite:

- the reviewed case anchor `case:<id>`;
- directly linked `alert:<id>`, `evidence:<id>`, `recommendation:<id>`, `action_request:<id>`, `approval_decision:<id>`, `action_execution:<id>`, `reconciliation:<id>`, `source_health:<id>`, or `ai_trace:<id>` records when present;
- explicit `gap:<gap-type>` citations for missing owner, stale source-health, receipt without reconciliation, conflicting evidence, and missing citation posture;
- `docs/automation/ai-agent-registry.json`;
- `docs/automation/ai-tool-registry.json`;
- `docs/automation/ai-disabled-degraded-mode-contract.json`.

## Disabled And Degraded Behavior

If AI advisory posture is disabled or degraded, the agent returns bounded fallback output. It keeps the non-AI review workflow available from authoritative records, does not create AI traces, and does not generate gap items.

If reviewed evidence payloads are missing, malformed, uncited, mismatched, AI-created truth, unsupported, or contract-mismatched, the agent fails closed with explicit unresolved reasons rather than inventing review posture.

Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, create evidence truth, bypass policy, hide citations, suppress uncertainty, choose authoritative truth, mark source health current, or mark evidence gaps resolved must be blocked.

## Validation

Run `python3 -m unittest control-plane.tests.test_phase60_4_evidence_gap_detector_agent`.

Run `bash scripts/verify-phase-60-4-evidence-gap-detector-agent.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1273 --config <supervisor-config-path>`.

## Non-Goals

- No autonomous approval, execution, reconciliation, case closure, detector activation, source-truth creation, evidence-truth creation, conflict resolution, policy bypass, or production write authority is introduced.
- No AI output, detector output, registry row, verifier output, issue-lint output, UI state, browser state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, prompt text, or model output becomes authoritative workflow truth.
- No Phase 61 SIEM breadth, Phase 62 SOAR breadth, Phase 66 RC proof, Beta, RC, GA, commercial replacement readiness, model marketplace, provider marketplace, prompt marketplace, tool marketplace, or customer-private prompt/data handling is implemented.
