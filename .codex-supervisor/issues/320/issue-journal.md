# Issue #320: design: define the identity-grounded analyst-assistant boundary on top of control-plane records and reviewed context

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/320
- Branch: codex/issue-320
- Workspace: .
- Journal: .codex-supervisor/issues/320/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: d86b7e62ce43866f15c7733499906870befec5bc
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-08T23:19:01.221Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 15 needed a reviewed, advisory-only assistant boundary doc set plus local verification that fails closed on missing identity-grounding and alias-ambiguity rules.
- What changed: Added Phase 15 boundary design and validation docs, a unittest guard for the docs, focused shell verifiers, and CI workflow hooks for the new validation and workflow-coverage steps.
- Current blocker: None.
- Next exact step: Review the diff for any wording or policy drift, then commit the Phase 15 boundary package.
- Verification gap: None for the focused scope; the new unit test, verifier, shell harness, and workflow coverage guard all passed.
- Files touched: `docs/phase-15-identity-grounded-analyst-assistant-boundary.md`, `docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md`, `control-plane/tests/test_phase15_identity_grounded_analyst_assistant_boundary_docs.py`, `scripts/verify-phase-15-identity-grounded-analyst-assistant-boundary.sh`, `scripts/test-verify-phase-15-identity-grounded-analyst-assistant-boundary.sh`, `scripts/test-verify-ci-phase-15-workflow-coverage.sh`, `.github/workflows/ci.yml`
- Rollback concern: Low; the change is isolated to Phase 15 boundary docs, verification wrappers, and CI wiring.
- Last focused command: `python3 -m unittest control-plane.tests.test_phase15_identity_grounded_analyst_assistant_boundary_docs && bash scripts/test-verify-phase-15-identity-grounded-analyst-assistant-boundary.sh && bash scripts/test-verify-ci-phase-15-workflow-coverage.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
