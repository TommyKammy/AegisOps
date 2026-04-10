# Issue #360: implementation: align the first-boot control-plane service command with the approved live runtime boundary

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/360
- Branch: codex/issue-360
- Workspace: .
- Journal: .codex-supervisor/issues/360/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: aa68f66070a2d9b00909162c39d577cd66693cee
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T00:31:22.923Z

## Latest Codex Summary
- Replaced the first-boot control-plane compose command with the long-running `python3 main.py serve` runtime surface, kept `python3 main.py runtime` as a read-only snapshot CLI, and tightened Phase 16 regression coverage so first boot fails closed if compose points back at the one-shot renderer.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The first-boot compose surface drifted to the read-only `runtime` snapshot CLI, so the boot contract could claim a live control-plane service while launching a process that prints JSON and exits.
- What changed: Added a long-running `serve` command in `control-plane/main.py` with `/healthz`, `/readyz`, and `/runtime` HTTP endpoints; switched `control-plane/deployment/first-boot/docker-compose.yml` to `python3 main.py serve`; updated `scripts/verify-phase-16-first-boot-contract.sh`; expanded CLI and Phase 16 verifier regression tests; refreshed `control-plane/README.md` to distinguish `serve` from `runtime`.
- Current blocker: none
- Next exact step: Commit the checkpoint, then leave the branch ready for supervisor review or follow-up verification.
- Verification gap: Did not exercise the long-running server against live Docker Compose or a live PostgreSQL-backed first-boot environment; coverage is unit-level plus repository contract verification.
- Files touched: .codex-supervisor/issues/360/issue-journal.md; control-plane/README.md; control-plane/deployment/first-boot/docker-compose.yml; control-plane/main.py; control-plane/tests/test_cli_inspection.py; control-plane/tests/test_phase16_first_boot_verifier.py; scripts/verify-phase-16-first-boot-contract.sh
- Rollback concern: Reverting only the compose command without also reverting the verifier and CLI changes would restore the false-positive first-boot service claim.
- Last focused command: python3 -m unittest control-plane.tests.test_phase16_first_boot_verifier control-plane.tests.test_cli_inspection
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
