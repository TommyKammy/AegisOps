# Issue #209: documentation: mark OpenSearch, Sigma, and n8n assets as transitional or optional in README and repository baseline

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/209
- Branch: codex/issue-209
- Workspace: .
- Journal: .codex-supervisor/issues/209/issue-journal.md
- Current phase: repairing_ci
- Attempt count: 2 (implementation=1, repair=1)
- Last head SHA: c5a765425c532ff5f923f90fbc37fa29de18b3c6
- Blocked reason: none
- Last failure signature: verify:fail
- Repeated failure signature count: 3
- Updated at: 2026-04-06T01:51:19Z

## Latest Codex Summary
Updated [README.md](README.md) and [docs/repository-structure-baseline.md](docs/repository-structure-baseline.md) to replace the legacy OpenSearch/Sigma/n8n-centered framing with the governed control-plane thesis, and to explicitly mark the existing top-level tree as transitional pending a later ADR. I also added a focused verifier plus fixture test at [scripts/verify-readme-and-repository-structure-control-plane-thesis.sh](scripts/verify-readme-and-repository-structure-control-plane-thesis.sh) and [scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh](scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh).

Committed as `c5a7654` (`docs: mark legacy substrate assets transitional`), pushed to `origin/codex/issue-209`, and opened draft PR [#216](https://github.com/TommyKammy/AegisOps/pull/216).

Summary: README and repository baseline now describe OpenSearch, Sigma, and n8n as optional/transitional, with focused regression verification added and draft PR #216 opened.
State hint: pr_open
Blocked reason: none
Tests: `bash scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh`; `bash scripts/verify-readme-and-repository-structure-control-plane-thesis.sh`; `bash scripts/verify-repository-structure-doc.sh`; `rg -n "transitional|optional|non-core|Wazuh|Shuffle|control plane" README.md docs/repository-structure-baseline.md`
Next action: wait for review on draft PR #216 and address any feedback
Failure signature: verify:fail

## Active Failure Context
- Category: checks
- Summary: PR #216 has failing checks.
- Command or source: gh pr checks
- Reference: https://github.com/TommyKammy/AegisOps/pull/216
- Details:
  - verify (fail/FAILURE) https://github.com/TommyKammy/AegisOps/actions/runs/24015400838/job/70033929889

## Codex Working Notes
### Current Handoff
- Hypothesis: The failing `verify` check came from stale README cross-link contracts in existing Phase 8 and Phase 9 validation scripts, not from the new control-plane-thesis verifier.
- What changed: Reproduced the GitHub Actions failure locally, restored the exact n8n-specific schema-boundary sentence required by Phase 8 in `README.md`, and updated the stale Phase 9 verifier plus its fixture test to require the current reviewed `postgres/control-plane/` README wording instead of the older placeholder-only text.
- Current blocker: none
- Next exact step: Commit the README and Phase 9 verifier repair, push `codex/issue-209`, and watch PR #216 for a green rerun.
- Verification gap: GitHub Actions has not rerun on the repaired commit yet; local workflow-equivalent verification is green.
- Files touched: README.md; scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh; scripts/test-verify-phase-9-control-plane-runtime-boundary-validation.sh; .codex-supervisor/issues/209/issue-journal.md
- Rollback concern: Low; changes are documentation and doc-verifier only, with no repository tree or runtime behavior changes.
- Last focused command: local workflow-equivalent `verify` command set from `.github/workflows/ci.yml`, plus `bash scripts/verify-readme-and-repository-structure-control-plane-thesis.sh` and `bash scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh`
### Scratchpad
- Reproduced failure 1 from Actions log: `scripts/verify-phase-8-control-plane-foundation-validation.sh` required `That schema boundary remains separate from n8n-owned PostgreSQL metadata and execution-state tables, and future rollout, access-control, and index-tuning work stays explicit.` while `README.md` had broader `substrate-owned metadata` wording.
- Reproduced failure 2 locally after fixing Phase 8: `scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh` still required the older placeholder-only `postgres/control-plane/` README sentence and conflicted with the reviewed Phase 8 baseline.
- Local verification run now passes the full `.github/workflows/ci.yml` `verify` job command set, including Python unit tests and focused shell tests, plus the new README and repository-structure thesis verifier and fixture test.
- Keep this section short. The supervisor may compact older notes automatically.
