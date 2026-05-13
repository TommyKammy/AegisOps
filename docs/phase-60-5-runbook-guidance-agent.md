# Phase 60.5 Runbook Guidance Agent

This phase adds the cited runbook guidance agent for Daily AI Operations.

The runtime entry point is `aegisops.control_plane.assistant.runbook_guidance.build_runbook_guidance`.

The agent suggests reviewed runbook steps from `docs/runbook.md` and directly linked AegisOps records only. It can render operator-visible `suggested`, `skipped`, `completed`, `blocked`, and `needs_review` posture, but completion ownership remains `operator` and guidance output never counts as workflow progress.

The agent uses the Phase 60.5 `runbook_guidance` tool registration in `docs/automation/ai-tool-registry.json`.

Required citations:

- `docs/automation/ai-agent-registry.json`;
- `docs/automation/ai-tool-registry.json`;
- `docs/runbook.md`;
- a reviewed `runbook:docs/runbook.md` record proving the runbook source was part of the reviewed context;
- directly linked reviewed AegisOps records explicitly bound to the review anchor, such as `case:<id>`, `evidence:<id>`, and `source_health:<source>`;
- the specific reviewed runbook section behind each suggested step, such as `docs/runbook.md#2.2`.

The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, mark runbook steps complete, convert suggestions into workflow progress, suppress uncertainty, hide citations, or treat runbook guidance as workflow truth.

If AI advisory posture is disabled or degraded, the agent returns bounded fallback output and keeps the non-AI runbook workflow available.

Each emitted step must include a display title and linked reviewed-record citations. Linked and blocked-by citations must reference reviewed records explicitly bound to the review anchor. `blocked` posture may only be derived from a linked reviewed `source_health:<source>` record whose source health is degraded.

If reviewed runbook payloads are missing, empty, malformed, uncited, stale without review posture, mismatched, unbound to the review anchor, AI-owned completion truth, unsupported, contract-mismatched, missing the reviewed runbook record, missing linked citations, or blocked by unverified sources, the agent fails closed with explicit unresolved reasons rather than inventing guidance posture.

Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress uncertainty, mark the runbook complete, complete workflow state, or execute runbook actions must be blocked.

Verification:

- Run `python3 -m unittest control-plane.tests.test_phase60_5_runbook_guidance_agent`.
- Run `bash scripts/verify-phase-60-5-runbook-guidance-agent.sh`.
- Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.
- Run `bash scripts/verify-publishable-path-hygiene.sh`.
- Run `node <codex-supervisor-root>/dist/index.js issue-lint 1274 --config <supervisor-config-path>`.
