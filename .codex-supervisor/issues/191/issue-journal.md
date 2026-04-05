# Issue #191: validation: add Phase 9 control-plane runtime slice validation and CI coverage

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/191
- Branch: codex/issue-191
- Workspace: .
- Journal: .codex-supervisor/issues/191/issue-journal.md
- Current phase: repairing_ci
- Attempt count: 3 (implementation=2, repair=1)
- Last head SHA: 0ebfe66a79ebe1843ad78506effb913fcda58a85
- Blocked reason: none
- Last failure signature: verify:fail
- Repeated failure signature count: 1
- Updated at: 2026-04-05T07:25:13.439Z

## Latest Codex Summary
Pushed `codex/issue-191` to `origin` and opened draft PR [#200](https://github.com/TommyKammy/AegisOps/pull/200) against `main` for the Phase 9 validation/CI coverage change set at `0ebfe66a79ebe1843ad78506effb913fcda58a85`. The GitHub connector could not create the PR due to a 403 integration restriction, so I used `gh pr create` as fallback.

I also updated the handoff in [`issue-journal.md`](.codex-supervisor/issues/191/issue-journal.md) to reflect the new draft-PR state and the remaining CI gap. No code changes were made this turn beyond that journal update.

Summary: Pushed branch `codex/issue-191`, opened draft PR `#200`, and updated the issue journal handoff to `pr_open` with CI pending.
State hint: pr_open
Blocked reason: none
Tests: Not run this turn; prior focused verification remains `bash scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh`, `bash scripts/test-verify-phase-9-control-plane-runtime-boundary-validation.sh`, `bash scripts/test-verify-ci-phase-9-workflow-coverage.sh`, and `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
Next action: Monitor PR #200 CI and address any failing checks or review feedback.
Failure signature: verify:fail

## Active Failure Context
- Category: checks
- Summary: PR #200 has failing checks.
- Command or source: gh pr checks
- Reference: https://github.com/TommyKammy/AegisOps/pull/200
- Details:
  - verify (fail/FAILURE) https://github.com/TommyKammy/AegisOps/actions/runs/23996700701/job/69985879574

## Codex Working Notes
### Current Handoff
- Hypothesis: The failing `verify` job was caused by exact-string documentation drift rather than workflow wiring. The first concrete failure was `scripts/verify-control-plane-schema-skeleton.sh` on `postgres/control-plane/README.md`, and rerunning the full local verifier block exposed a second exact-line drift in `README.md` required by the Phase 8 foundation validator.
- What changed: Restored the exact PostgreSQL control-plane boundary sentence in `README.md` required by `scripts/verify-phase-8-control-plane-foundation-validation.sh` and added the runtime-ready schema-baseline sentence to `postgres/control-plane/README.md` while preserving the existing exact line required by `scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh` and `scripts/verify-control-plane-schema-skeleton.sh`.
- Current blocker: none
- Next exact step: Push the README verifier repair on `codex/issue-191`, then monitor PR #200 for a fresh `verify` rerun.
- Verification gap: Remote GitHub Actions has not rerun on the repaired commit yet; local verification is now stronger than the original failing job because the exact `Run documentation and skeleton verifiers` block was rerun end to end.
- Files touched: `README.md`, `postgres/control-plane/README.md`
- Rollback concern: Low; changes tighten existing verifier expectations and CI coverage without changing runtime behavior.
- Last focused commands: `gh run view 23996700701 --job 69985879574 --log`; `bash scripts/verify-control-plane-schema-skeleton.sh`; `bash scripts/verify-phase-8-control-plane-foundation-validation.sh`; `bash scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh`; `bash -euo pipefail <<'EOF' ... verify block from .github/workflows/ci.yml ... EOF`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Local reproduction details: GitHub Actions run `23996700701` failed first with `Control-plane schema README must describe the reviewed runtime-ready baseline.` After fixing that line family, the full local verifier block failed on `README.md` with `Missing required line ... reviewed AegisOps-owned control-plane schema baseline and migration assets`, which is now restored.
