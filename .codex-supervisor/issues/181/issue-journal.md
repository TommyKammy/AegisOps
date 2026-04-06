# Issue #181: design: define the control-plane runtime service boundary and repository placement

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/181
- Branch: codex/issue-181
- Workspace: .
- Journal: .codex-supervisor/issues/181/issue-journal.md
- Current phase: repairing_ci
- Attempt count: 3 (implementation=2, repair=1)
- Last head SHA: c9c590a87e9ee13784e4168d35d5e9a4cc76c5f2
- Blocked reason: none
- Last failure signature: verify:fail
- Repeated failure signature count: 1
- Updated at: 2026-04-04T20:26:57.300Z

## Latest Codex Summary
Reproduced the failing `verify` check from PR [#193](https://github.com/TommyKammy/AegisOps/pull/193) and traced it to an exact-string drift in `README.md` after the broader Phase 8 foundation validator was included in CI merge validation.

Updated `README.md` to restore the approved placeholder PostgreSQL boundary wording, then aligned `scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh` with that same approved baseline so the issue-specific verifier no longer conflicts with the broader CI contract. Focused local verification now passes for the reproduced blocker and the Phase 9 design-boundary checks.

Summary: Repaired the PR `verify` failure by restoring the approved `README.md` placeholder-boundary wording and syncing the Phase 9 validator to the same exact baseline.
State hint: repairing_ci
Blocked reason: none
Tests: `bash scripts/test-verify-control-plane-runtime-service-boundary-doc.sh`; `bash scripts/test-verify-repository-skeleton.sh`; `bash scripts/verify-repository-skeleton.sh`; `bash scripts/verify-repository-structure-doc.sh`; `bash scripts/verify-control-plane-runtime-service-boundary-doc.sh`; `bash scripts/verify-phase-8-control-plane-foundation-validation.sh`; `bash scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh`; `rg -n 'control-plane|OpenSearch|n8n|PostgreSQL|repository' docs README.md`
Next action: Commit and push the CI repair on `codex/issue-181`, then monitor PR `#193` for the rerun of `verify`.
Failure signature: verify:fail

## Active Failure Context
- Category: checks
- Summary: PR #193 has failing checks.
- Command or source: gh pr checks
- Reference: https://github.com/TommyKammy/AegisOps/pull/193
- Details:
  - verify (fail/FAILURE) https://github.com/TommyKammy/AegisOps/actions/runs/23986837977/job/69960062480

## Codex Working Notes
### Current Handoff
- Hypothesis: The failing PR merge check came from baseline drift, not a missing design artifact: the merged CI suite enforced newer Phase 8 `README.md` wording than this branch carried, and the Phase 9 verifier still enforced the older text.
- What changed: Reproduced the failing merge-check locally with `bash scripts/verify-phase-8-control-plane-foundation-validation.sh`, updated `README.md` to the approved placeholder PostgreSQL boundary wording, and changed `scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh` to require that same wording so Phase 8 and Phase 9 checks agree.
- Current blocker: none
- Next exact step: Commit and push the repair so PR `#193` reruns `verify`, then confirm the failing check clears.
- Verification gap: I did not run the entire GitHub Actions verify workflow locally; I ran the reproduced blocker plus the focused Phase 8, Phase 9, repository-structure, repository-skeleton, and boundary verifier/test commands that cover the changed README and verifier paths.
- Files touched: .codex-supervisor/issues/181/issue-journal.md; README.md; scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh
- Rollback concern: Reverting this repair would restore the README/verifier wording conflict and leave PR `#193` failing the merge-time verify suite even though the design artifacts themselves remain present.
- Last focused command: bash scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh
- Exact failures observed: `gh pr checks 193 --json ...` and the Actions log for run `23986837977` showed `Missing required line in .../README.md: Within \`postgres/\`, the \`control-plane/\` directory reserves the repository home for placeholder AegisOps-owned control-plane schema and migration assets. It does not introduce a live datastore or runtime migration flow.` Local reproduction with `bash scripts/verify-phase-8-control-plane-foundation-validation.sh` failed with the same message before the README fix.
- Commands run this turn: `sed -n '1,220p' <redacted-local-path>`; `sed -n '1,220p' <redacted-local-path>`; `sed -n '1,260p' .codex-supervisor/issues/181/issue-journal.md`; `sed -n '1,220p' <redacted-local-path>`; `gh auth status`; `gh pr checks 193 --json name,state,bucket,link,startedAt,completedAt,workflow`; `python3 <redacted-local-path> --repo . --pr 193 --json`; `git status --short --branch`; `sed -n '1,240p' README.md`; `sed -n '1,240p' docs/repository-structure-baseline.md`; `sed -n '1,220p' scripts/verify-repository-structure-doc.sh`; `bash scripts/verify-repository-structure-doc.sh`; `git fetch origin main`; `git rev-parse HEAD origin/main`; `sed -n '1,220p' scripts/verify-phase-8-control-plane-foundation-validation.sh`; `bash scripts/verify-phase-8-control-plane-foundation-validation.sh`; `sed -n '1,240p' scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh`; `sed -n '1,220p' docs/phase-9-control-plane-runtime-boundary-validation.md`; `sed -n '1,220p' docs/control-plane-runtime-service-boundary.md`; `rg -n "reviewed control-plane schema and migration assets|runtime application root|placeholder AegisOps-owned control-plane schema and migration assets|runtime migration flow" scripts docs README.md control-plane postgres`; `bash scripts/test-verify-control-plane-runtime-service-boundary-doc.sh`; `bash scripts/test-verify-repository-skeleton.sh`; `bash scripts/verify-repository-skeleton.sh`; `bash scripts/verify-control-plane-runtime-service-boundary-doc.sh`; `bash scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh`; `rg -n 'control-plane|OpenSearch|n8n|PostgreSQL|repository' docs README.md`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
