# Phase 60.1 Setup Doctor Explanation Agent

- **Status**: Implemented focused Phase 60 slice
- **Date**: 2026-05-13
- **Owner**: AegisOps maintainers
- **Related Issues**: #1269, #1270

This contract defines the bounded setup and doctor explanation agent for Phase 60 daily operations. It explains existing setup, dependency, degraded-source, AI-disabled, and doctor posture failures from cited AegisOps doctor/supportability records without automatic repair authority.

The runtime entry point is `aegisops.control_plane.assistant.setup_doctor_explanation.build_setup_doctor_explanation`.

## Authority Boundary

The setup doctor explanation agent is read-only, cited, registered-tool-backed, reviewable, and subordinate to AegisOps records.

The agent may explain doctor states, cite supportability records, cite registered Phase 59 registry artifacts, surface evidence gaps, and provide safe next steps for operator review.

The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, mutate secrets, restart services, repair the stack, change source posture, or treat support output as workflow, release, gate, restore, limitation, or closeout truth.

## Registered Tool Linkage

The agent uses the existing Phase 59 `doctor_explanation` tool registration in `docs/automation/ai-tool-registry.json`.

Every explanation output must cite:

- the doctor state family anchor, such as `doctor:wazuh` or `doctor:stale_source`;
- `docs/phase-58-1-aegisops-doctor-contract.md`;
- `docs/automation/ai-agent-registry.json`;
- `docs/automation/ai-tool-registry.json`;
- `docs/automation/ai-disabled-degraded-mode-contract.json`.

## Disabled And Degraded Behavior

If AI advisory posture is disabled or degraded, the agent returns bounded fallback output. It must keep non-AI workflow surfaces available from authoritative AegisOps records, must not create AI traces, and must not generate recommendations or action drafts.

If doctor evidence is missing or malformed, the agent fails closed with explicit unresolved reasons and bounded fallback guidance rather than inventing setup guidance.

Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress uncertainty, repair the stack, rotate secrets, restart services, or change source posture must be blocked.

## Validation

Run `python3 -m unittest control-plane.tests.test_phase60_1_setup_doctor_explanation_agent`.

Run `bash scripts/verify-phase-60-1-setup-doctor-explanation-agent.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1270 --config <supervisor-config-path>`.

## Non-Goals

- No automatic repair, restart, secret mutation, source mutation, approval, execution, reconciliation, detector activation, source-truth creation, policy bypass, or production write authority is introduced.
- No AI output, doctor output, supportability output, registry row, verifier output, issue-lint output, UI state, browser state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, prompt text, or model output becomes authoritative workflow truth.
- No Phase 61 SIEM breadth, Phase 62 SOAR breadth, Phase 66 RC proof, Beta, RC, GA, commercial replacement readiness, model marketplace, provider marketplace, prompt marketplace, tool marketplace, or customer-private prompt/data handling is implemented.
