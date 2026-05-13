# Phase 60.2 Today Queue Digest Agent

- **Status**: Implemented focused Phase 60 slice
- **Date**: 2026-05-13
- **Owner**: AegisOps maintainers
- **Related Issues**: #1269, #1271

This contract defines the bounded Today queue digest agent for Phase 60 daily operations. It summarizes reviewed Today analyst queue records with citations, stale/degraded posture, unresolved work, and explicit evidence gaps without changing queue priority, task state, case state, approval state, execution state, reconciliation state, or workflow routing.

The runtime entry point is `aegisops.control_plane.assistant.today_queue_digest.build_today_queue_digest`.

## Authority Boundary

The Today queue digest agent is read-only, cited, registered-tool-backed, reviewable, and subordinate to reviewed AegisOps records.

The agent may summarize reviewed queue records, cite directly linked alerts, cases, evidence, source-health posture, reconciliations, action reviews, handoff context, and explicit missing-evidence gaps.

The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, change queue priority, mark tasks complete, suppress stale or degraded work, hide missing evidence, or treat digest output as workflow truth.

## Registered Tool Linkage

The agent uses the Phase 60.2 `today_queue_digest` tool registration in `docs/automation/ai-tool-registry.json`.

Every digest output must cite:

- the reviewed analyst queue anchor `queue:analyst_review`;
- directly linked `alert:<id>` and `case:<id>` records when present;
- linked `evidence:<id>` records or explicit `missing_evidence:<alert-id>` gaps;
- degraded `source_health:<source>` context when degraded source posture is present;
- directly linked `reconciliation:<correlation-key>` records when present;
- `handoff:<alert-id>` context only when a reviewed handoff object is present;
- `docs/automation/ai-agent-registry.json`;
- `docs/automation/ai-tool-registry.json`;
- `docs/automation/ai-disabled-degraded-mode-contract.json`.

## Disabled And Degraded Behavior

If AI advisory posture is disabled or degraded, the agent returns bounded fallback output. It keeps the non-AI Today workflow available from authoritative queue records, does not create AI traces, and does not generate digest items.

If queue evidence is missing, malformed, unreviewed, or uncited, the agent fails closed with explicit unresolved reasons rather than inventing a digest.

Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress stale/degraded work, suppress uncertainty, change queue priority, or mark tasks complete must be blocked.

## Validation

Run `python3 -m unittest control-plane.tests.test_phase60_2_today_queue_digest_agent`.

Run `bash scripts/verify-phase-60-2-today-queue-digest-agent.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1271 --config <supervisor-config-path>`.

## Non-Goals

- No autonomous approval, execution, reconciliation, case closure, detector activation, source-truth creation, queue priority mutation, task completion, policy bypass, or production write authority is introduced.
- No AI output, digest output, registry row, verifier output, issue-lint output, UI state, browser state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, prompt text, or model output becomes authoritative workflow truth.
- No Phase 61 SIEM breadth, Phase 62 SOAR breadth, Phase 66 RC proof, Beta, RC, GA, commercial replacement readiness, model marketplace, provider marketplace, prompt marketplace, tool marketplace, or customer-private prompt/data handling is implemented.
