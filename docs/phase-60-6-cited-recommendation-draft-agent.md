# Phase 60.6 Cited Recommendation Draft Agent

This phase adds the cited recommendation draft agent for Daily AI Operations.

The runtime entry point is `aegisops.control_plane.assistant.cited_recommendation_draft.build_cited_recommendation_draft`.

The agent drafts reviewable recommendation text from directly linked queue, case, evidence, runbook, existing recommendation, source-health, and AI trace context only. It can render operator-visible `accepted`, `rejected`, `corrected`, and `unresolved` feedback posture, but feedback remains review context only and never becomes workflow truth.

The agent uses the Phase 60.6 `recommendation_draft` tool registration in `docs/automation/ai-tool-registry.json`.

Required citations:

- `docs/automation/ai-agent-registry.json`;
- `docs/automation/ai-tool-registry.json`;
- directly linked reviewed AegisOps records explicitly bound to the review anchor, such as `case:<id>`, `queue:<name>`, `evidence:<id>`, `runbook:<section>`, and `recommendation:<id>`;
- each recommendation draft's reviewed supporting citations.

The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, convert recommendation feedback into workflow truth, mark workflow complete, suppress uncertainty, hide citations, or force acceptance.

If AI advisory posture is disabled or degraded, the agent returns bounded fallback output and keeps the non-AI recommendation workflow available.

Each emitted draft must include display text, supporting citations, advisory-only flags, and explicit no-authority fields for approval, execution, reconciliation, and case closure. Corrected feedback must keep the operator correction visible as review context only. Unresolved, stale, or conflicting evidence posture must remain visible and keeps emitted draft feedback unresolved.

If recommendation context payloads are missing, empty, malformed, uncited, unsupported, contract-mismatched, unbound to the review anchor, AI-created recommendation context, unsupported feedback posture, missing correction text, missing required draft citations, or linked to untrusted draft citations, the agent fails closed with explicit unresolved reasons rather than inventing feedback posture.

Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress uncertainty, force acceptance, hide rejected or corrected state, or complete workflow state must be blocked.

Verification:

- Run `python3 -m unittest control-plane.tests.test_phase60_6_cited_recommendation_draft_agent`.
- Run `bash scripts/verify-phase-60-6-cited-recommendation-draft-agent.sh`.
- Run `npm test -- --run src/app/OperatorRoutes.test.tsx` from `apps/operator-ui`.
- Run `npm run typecheck --workspace @aegisops/operator-ui`.
- Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.
- Run `bash scripts/verify-publishable-path-hygiene.sh`.
- Run `node <codex-supervisor-root>/dist/index.js issue-lint 1275 --config <supervisor-config-path>`.
