# Issue #364: design: define the concrete Phase 17 runtime config contract and boot command expectations

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/364
- Branch: codex/issue-364
- Workspace: .
- Journal: .codex-supervisor/issues/364/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: b993d1bb99faeed48b35cebd9f71d2b767c9f4ac
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T02:39:49.555Z

## Latest Codex Summary
Added the Phase 17 contract doc at [docs/phase-17-runtime-config-contract-and-boot-command-expectations.md](docs/phase-17-runtime-config-contract-and-boot-command-expectations.md), plus a focused reproducing test at [control-plane/tests/test_phase17_runtime_config_contract_docs.py](control-plane/tests/test_phase17_runtime_config_contract_docs.py). The doc makes the first-boot runtime keys, reviewed defaults, fail-closed rules, migration bootstrap sequence, and reverse-proxy-only exposure model explicit, and it calls out which Phase 16 placeholders are now concrete versus still deferred.

I also added the new contract to [README.md](README.md) and [docs/documentation-ownership-map.md](docs/documentation-ownership-map.md), updated the issue journal at [.codex-supervisor/issues/364/issue-journal.md](.codex-supervisor/issues/364/issue-journal.md), and committed the checkpoint as `b993d1b` with message `Define Phase 17 runtime config contract`.

Verification ran clean:
`python3 -m unittest control-plane.tests.test_phase17_runtime_config_contract_docs`
`python3 -m unittest control-plane.tests.test_phase16_bootstrap_contract_docs`
`python3 -m unittest control-plane.tests.test_phase16_first_boot_verifier`

Summary: Added and verified the missing Phase 17 runtime config and boot-command contract, anchored to the existing Phase 16 first-boot floor.
State hint: implementing
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase17_runtime_config_contract_docs`; `python3 -m unittest control-plane.tests.test_phase16_bootstrap_contract_docs`; `python3 -m unittest control-plane.tests.test_phase16_first_boot_verifier`
Next action: Decide whether to add a repo-level verifier/validation snapshot for the new Phase 17 contract and open a draft PR from commit `b993d1b`.
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The Phase 17 contract doc is present and tested, but the checkpoint still benefits from a repo-level verifier and validation snapshot so reviewers can confirm the runtime contract without relying only on a single Python doc test.
- What changed: Added `docs/phase-17-runtime-config-contract-validation.md`, `scripts/verify-phase-17-runtime-config-contract.sh`, and `scripts/test-verify-phase-17-runtime-config-contract.sh`, then linked the validation doc from `README.md` and `docs/documentation-ownership-map.md`.
- Current blocker: none
- Next exact step: Commit the Phase 17 verifier/validation checkpoint on `codex/issue-364`, push the branch, and open a draft PR from that checkpoint.
- Verification gap: The requested `Phase 16-21 Epic Roadmap.md` comparison target is still unavailable in the local worktree, so the validation snapshot records that deviation instead of claiming roadmap review was completed.
- Files touched: `docs/phase-17-runtime-config-contract-validation.md`, `scripts/verify-phase-17-runtime-config-contract.sh`, `scripts/test-verify-phase-17-runtime-config-contract.sh`, `README.md`, `docs/documentation-ownership-map.md`, `.codex-supervisor/issues/364/issue-journal.md`
- Rollback concern: Low; changes remain documentation and verification only, but the new verifier now treats direct backend publication, widened startup prerequisites, and missing fail-closed contract language as review failures.
- Last focused command: `bash scripts/verify-phase-17-runtime-config-contract.sh && bash scripts/test-verify-phase-17-runtime-config-contract.sh && python3 -m unittest control-plane.tests.test_phase17_runtime_config_contract_docs control-plane.tests.test_phase16_bootstrap_contract_docs control-plane.tests.test_phase16_first_boot_verifier && bash scripts/verify-phase-16-first-boot-contract.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
