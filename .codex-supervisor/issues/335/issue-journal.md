# Issue #335: validation: extend adversarial coverage to the assistant response path for advisory outputs

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/335
- Branch: codex/issue-335
- Workspace: .
- Journal: .codex-supervisor/issues/335/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: e1737022f1e383ac21c8e44e9f1be70c49940308
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-09T10:04:48.986Z

## Latest Codex Summary
- Added focused assistant response-path coverage for alias-only identity ambiguity and authority or scope-overreach recommendation text, then updated the advisory-output builder and Phase 15 verification wiring to fail closed on those cases.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The Phase 15 boundary docs already required fail-closed response rendering, but the live assistant advisory-output path still marked alias-only identity context and authority-claiming recommendation text as ready.
- What changed: Added two focused runtime tests in `control-plane/tests/test_service_persistence.py`, patched `control-plane/aegisops_control_plane/service.py` to fail closed on alias-only identity metadata and authority or scope-expansion language in intended outcomes, and wired those runtime tests into the Phase 15 docs/CI/verifier guardrails.
- Current blocker: none
- Next exact step: Commit the verified Phase 15 response-path validation changes on `codex/issue-335`.
- Verification gap: none for the local Phase 15 slice; focused runtime tests, Phase 15 verifiers, and full `unittest discover` all passed locally.
- Files touched: `.github/workflows/ci.yml`; `control-plane/aegisops_control_plane/service.py`; `control-plane/tests/test_service_persistence.py`; `docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md`; `scripts/test-verify-ci-phase-15-workflow-coverage.sh`; `scripts/test-verify-phase-15-identity-grounded-analyst-assistant-boundary.sh`; `scripts/verify-phase-15-identity-grounded-analyst-assistant-boundary.sh`
- Rollback concern: The new authority/scope heuristic is intentionally conservative and currently keyed off explicit approval/execution/reconciliation and broad-scope terms in recommendation `intended_outcome` text.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
