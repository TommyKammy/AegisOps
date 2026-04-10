# Issue #364: design: define the concrete Phase 17 runtime config contract and boot command expectations

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/364
- Branch: codex/issue-364
- Workspace: .
- Journal: .codex-supervisor/issues/364/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 70dab8746bea43e64b0fe4c951bd8f00c5043aa2
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T02:33:57.788Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The Phase 16 first-boot floor is already defined and verified locally, but the repository has no Phase 17 artifact that turns that floor into an explicit runtime config contract and boot command expectation for real bring-up work.
- What changed: Added a focused reproducing test for the missing Phase 17 contract doc, confirmed the failure, then added `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md` plus README and documentation-ownership references.
- Current blocker: none
- Next exact step: Commit the Phase 17 contract doc checkpoint on `codex/issue-364`, then decide whether to add a repository verifier script or open a draft PR from this checkpoint.
- Verification gap: No repo-level shell verifier or validation snapshot was added for the new Phase 17 doc in this turn; verification currently relies on focused Python doc tests and adjacent Phase 16 first-boot tests.
- Files touched: `control-plane/tests/test_phase17_runtime_config_contract_docs.py`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, `README.md`, `docs/documentation-ownership-map.md`, `.codex-supervisor/issues/364/issue-journal.md`
- Rollback concern: Low; changes are documentation and test coverage only, but the new contract explicitly rejects direct backend publication and broadening first-boot prerequisites, so later runtime implementation must follow those constraints.
- Last focused command: `python3 -m unittest control-plane.tests.test_phase17_runtime_config_contract_docs control-plane.tests.test_phase16_bootstrap_contract_docs control-plane.tests.test_phase16_first_boot_verifier`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
