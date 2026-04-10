# Issue #359: implementation: enforce fail-closed migration-bootstrap and readiness gating in the first-boot entrypoint

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/359
- Branch: codex/issue-359
- Workspace: .
- Journal: .codex-supervisor/issues/359/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 8341f77120efc60147e5f16798ba5db1ca3e879c
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T00:09:49.132Z

## Latest Codex Summary
- Reproduced the issue with a focused unit test showing `control-plane-entrypoint.sh` returned success for a dummy command when only required env vars were present.
- Replaced the env-only handoff with fail-closed migration-bootstrap and readiness gating: required migration assets must exist, `psql` must be available, reviewed migrations must apply cleanly, and a minimal schema-readiness query must return `ready` before `exec "$@"`.
- Added focused regression coverage for both fail-closed behavior and a mocked success path, and updated the Phase 16 first-boot verifier expectations to lock the new contract in place.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The first-boot entrypoint was still honoring the old Phase 16 skeleton behavior and allowed startup on env validation alone, so a dummy command could bypass migration-bootstrap and readiness proof entirely.
- What changed: Added fail-closed gating in `control-plane/deployment/first-boot/control-plane-entrypoint.sh` for reviewed migration assets, `psql` availability, forward migration execution, and a minimal schema-readiness proof; tightened `control-plane/tests/test_phase16_bootstrap_contract_docs.py`; updated `scripts/verify-phase-16-first-boot-contract.sh` to require the new entrypoint contract lines.
- Current blocker: none
- Next exact step: Create a checkpoint commit on `codex/issue-359`, then continue with any broader local review only if new feedback appears.
- Verification gap: Focused Phase 16 verification is green, but no live PostgreSQL-backed end-to-end bring-up was run in this turn.
- Files touched: control-plane/deployment/first-boot/control-plane-entrypoint.sh; control-plane/tests/test_phase16_bootstrap_contract_docs.py; scripts/verify-phase-16-first-boot-contract.sh; .codex-supervisor/issues/359/issue-journal.md
- Rollback concern: The entrypoint now hard-fails if the migration mount or `psql` client is absent, so any local first-boot harness that relied on the previous placeholder pass-through must supply those reviewed prerequisites.
- Last focused command: python3 -m unittest control-plane.tests.test_phase16_bootstrap_contract_docs control-plane.tests.test_phase16_first_boot_verifier && bash scripts/test-verify-phase-16-first-boot-contract.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
