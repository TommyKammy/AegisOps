# Phase 59.4 AI Disabled And Degraded Mode Contract

- **Status**: Accepted disabled and degraded mode contract slice
- **Date**: 2026-05-11
- **Owner**: AegisOps maintainers
- **Related Issues**: #1252, #1256

This contract defines the AI disabled and degraded mode behavior before Phase 59 expands prompt fixtures, stale or conflicting evidence fixtures, trace queue UI/API implementation, closeout work, or Phase 60 daily AI operations.

It is limited to the Phase 59.4 AI disabled and degraded mode contract. It does not implement new model routing, provider selection, tool execution, trace queue behavior, daily AI operations, approval, execution, reconciliation, case closure, detector activation, source truth, production write authority, or commercial-readiness claims.

## 1. Required Mode Fields

Every disabled or degraded mode row must include mode, trigger, operator state, readiness posture, blocked AI generation flags, reason, explanation, safe next steps, authority effect, and disallowed authority.

The executable mode artifact lives in `docs/automation/ai-disabled-degraded-mode-contract.json`.

The mode artifact is a repo-owned policy artifact. It is not runtime truth, workflow truth, approval truth, execution truth, reconciliation truth, release truth, gate truth, closeout truth, or source truth.

## 2. Authority Boundary

AI remains advisory, registered, audited, cited, and subordinate to reviewed AegisOps records when available, and it produces no recommendations, action drafts, or trace state when disabled or degraded.

No disabled or degraded mode row may grant approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, automatic repair, workflow truth, or authority-widening capability.

Disabled and degraded AI posture must not block queue, case, evidence review, action review, reconciliation, doctor/supportability explanation fallback, or admin enablement posture surfaces that use authoritative AegisOps records.

Operator-facing state must explain AI unavailability without implying AI approval, automatic repair, source truth, reconciliation truth, case closure, or workflow completion.

This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.

## 3. Disabled And Degraded Modes

| Mode | Meaning | Required workflow posture |
| --- | --- | --- |
| `disabled` | Platform policy has intentionally disabled AI advisory generation. | Non-AI queue, case, evidence review, action review, reconciliation, supportability, and admin surfaces continue from authoritative records. |
| `degraded` | AI advisory generation is operationally unavailable, stale, partially trusted, or otherwise not safe to use. | Non-AI workflow continues and AI output remains unavailable until a reviewed healthy posture returns. |

These names identify AI advisory posture, not workflow lifecycle states with independent authority.

## 4. Non-AI Workflow Surface Requirements

The contract covers these non-AI surfaces:

- queue;
- case;
- evidence review;
- action review;
- reconciliation;
- doctor/supportability explanation fallback;
- admin enablement posture.

Each covered surface must keep its authoritative AegisOps record source, must declare AI as non-blocking, and must provide an operator-visible unavailable or degraded explanation when AI context is absent.

## 5. Verifier Requirements

The disabled/degraded verifier must fail when:

- the contract doc is missing;
- the mode artifact is missing or invalid JSON;
- disabled or degraded mode coverage is missing;
- any disabled or degraded mode allows AI generation, recommendation generation, action-draft generation, or trace creation;
- any required non-AI workflow surface is missing or depends on AI;
- disabled or degraded copy omits an operator-facing explanation;
- disabled or degraded copy implies AI approval, execution, reconciliation, case closure, detector activation, source truth, automatic repair, workflow truth, or authority widening;
- publishable artifacts contain workstation-local absolute paths.

## 6. Validation

Run `bash scripts/verify-phase-59-4-ai-disabled-degraded-mode-contract.sh`.

Run `bash scripts/test-verify-phase-59-4-ai-disabled-degraded-mode-contract.sh`.

Run `python3 -m unittest control-plane.tests.test_phase57_7_ai_enablement_admin_toggle`.

Run `python3 -m unittest control-plane.tests.test_phase58_1_doctor_contract.Phase581DoctorContractTests.test_doctor_contract_reports_degraded_source_and_ai_without_authority`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1256 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1252 --config <supervisor-config-path>`.

## 7. Non-Goals

- No new production write authority is introduced.
- No AI output, trace state, citation, registry row, mode artifact, verifier output, issue-lint output, browser state, UI state, demo data, Wazuh state, Shuffle state, ticket state, optional evidence, doctor output, supportability output, or prompt text becomes authoritative workflow truth.
- No Phase 60 daily AI operations behavior is implemented.
- No model/provider selection, billing, prompt marketplace, tool marketplace, or agent ecosystem breadth is implemented.
- No approval, execution, reconciliation, case closure, detector activation, source-truth creation, automatic repair, production write, or policy bypass is delegated to AI.
