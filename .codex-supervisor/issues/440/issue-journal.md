# Issue #440: validation: add end-to-end Phase 21 coverage for auth, restore, observability, and second-source onboarding

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/440
- Branch: codex/issue-440
- Workspace: .
- Journal: .codex-supervisor/issues/440/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 085bb1e7de8de976fda2c7e6cd7132022cece821
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-13T21:04:23.539Z

## Latest Codex Summary
- Added `control-plane/tests/test_phase21_end_to_end_validation.py` to cover Phase 21 auth fail-closed behavior, restore/readiness continuity, narrow Entra ID second-source onboarding, and preservation of the completed Phase 20 `notify_identity_owner` live path.
- Updated the Phase 21 validation doc, verifier scripts, and CI workflow so the new focused runtime proof is treated as a required validation artifact.
- Focused verification passed for the new Phase 21 suite, the Phase 21 verifier scripts, the Phase 20 workflow guard, and the relevant existing runtime/operator-surface/persistence/source-onboarding suites.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The repo already had most Phase 21 behavior, but it lacked one explicit end-to-end validation slice that packaged auth fail-closed, restore, observability, second-source onboarding, and preserved Phase 20 flow into a required artifact.
- What changed: Added `control-plane/tests/test_phase21_end_to_end_validation.py`; updated `docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md`; updated `control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py`, `control-plane/tests/test_phase21_production_like_hardening_boundary_validation.py`, `scripts/verify-phase-21-production-like-hardening-boundary.sh`, `scripts/test-verify-phase-21-production-like-hardening-boundary.sh`, `scripts/test-verify-ci-phase-21-workflow-coverage.sh`, and `.github/workflows/ci.yml` to require the new artifact.
- Current blocker: none
- Next exact step: Commit the focused validation changes on `codex/issue-440` and hand back with the passing verification set.
- Verification gap: No known local gap in the targeted Phase 21/Phase 20/runtime coverage that was requested for this turn.
- Files touched: `.github/workflows/ci.yml`, `control-plane/tests/test_phase21_end_to_end_validation.py`, `control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py`, `control-plane/tests/test_phase21_production_like_hardening_boundary_validation.py`, `docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md`, `scripts/test-verify-ci-phase-21-workflow-coverage.sh`, `scripts/test-verify-phase-21-production-like-hardening-boundary.sh`, `scripts/verify-phase-21-production-like-hardening-boundary.sh`
- Rollback concern: Low; changes are limited to validation/tests/docs/workflow wiring and do not modify control-plane runtime behavior.
- Last focused command: `python3 -m unittest control-plane.tests.test_phase21_runtime_auth_validation control-plane.tests.test_cli_inspection control-plane.tests.test_service_persistence control-plane.tests.test_phase20_low_risk_action_validation control-plane.tests.test_wazuh_adapter`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
