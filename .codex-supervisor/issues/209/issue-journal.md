# Issue #209: documentation: mark OpenSearch, Sigma, and n8n assets as transitional or optional in README and repository baseline

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/209
- Branch: codex/issue-209
- Workspace: .
- Journal: .codex-supervisor/issues/209/issue-journal.md
- Current phase: addressing_review
- Attempt count: 3 (implementation=1, repair=2)
- Last head SHA: 8edb1c21cb6bfda80f4ed3f39337d6cbb0e49941
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc548Yg0
- Repeated failure signature count: 1
- Updated at: 2026-04-06T01:57:18.552Z

## Latest Codex Summary
Validated CodeRabbit thread `PRRT_kwDOR2iDUc548Yg0` against the live branch and confirmed the finding: [scripts/verify-readme-and-repository-structure-control-plane-thesis.sh](scripts/verify-readme-and-repository-structure-control-plane-thesis.sh) existed, but [ci.yml](.github/workflows/ci.yml) did not invoke it. Updated the workflow to run both the verifier and its focused shell test so the README and repository-structure control-plane-thesis contract is enforced in CI.

Summary: Wired the control-plane-thesis verifier and its fixture test into the CI workflow to resolve the remaining review thread on PR #216.
State hint: local_review_fix
Blocked reason: none
Tests: Ran `bash scripts/verify-readme-and-repository-structure-control-plane-thesis.sh`; ran `bash scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh`; ran `rg -n "verify-readme-and-repository-structure-control-plane-thesis|test-verify-readme-and-repository-structure-control-plane-thesis" .github/workflows/ci.yml`
Next action: Commit and push the CI workflow review fix to `codex/issue-209`, then watch PR #216 for a clean rerun and resolve the review thread.
Failure signature: PRRT_kwDOR2iDUc548Yg0

## Active Failure Context
- Category: review
- Summary: 1 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/216#discussion_r3037658220
- Details:
  - scripts/verify-readme-and-repository-structure-control-plane-thesis.sh:74 summary=_⚠️ Potential issue_ | _🟠 Major_ 🧩 Analysis chain 🏁 Script executed: Repository: TommyKammy/AegisOps Length of output: 45 --- 🏁 Script executed: Repository: TommyKammy/Aegis... url=https://github.com/TommyKammy/AegisOps/pull/216#discussion_r3037658220

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining review blocker is valid and narrowly scoped to CI wiring; the new README/repository-structure verifier and its fixture test were not yet included in `.github/workflows/ci.yml`.
- What changed: Added `bash scripts/verify-readme-and-repository-structure-control-plane-thesis.sh` to the documentation verifier step and `bash scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh` to focused shell tests.
- Current blocker: none
- Next exact step: Commit the CI workflow repair, push `codex/issue-209`, and watch PR #216 for a green rerun before resolving the review thread.
- Verification gap: The updated workflow has only been verified locally with focused checks; GitHub Actions has not rerun on the CI-wiring fix yet.
- Files touched: .github/workflows/ci.yml; .codex-supervisor/issues/209/issue-journal.md
- Rollback concern: Low; changes are documentation and doc-verifier only, with no repository tree or runtime behavior changes.
- Last focused command: `bash scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh`
### Scratchpad
- Reproduced failure 1 from Actions log: `scripts/verify-phase-8-control-plane-foundation-validation.sh` required `That schema boundary remains separate from n8n-owned PostgreSQL metadata and execution-state tables, and future rollout, access-control, and index-tuning work stays explicit.` while `README.md` had broader `substrate-owned metadata` wording.
- Reproduced failure 2 locally after fixing Phase 8: `scripts/verify-phase-9-control-plane-runtime-boundary-validation.sh` still required the older placeholder-only `postgres/control-plane/` README sentence and conflicted with the reviewed Phase 8 baseline.
- Local verification run now passes the full `.github/workflows/ci.yml` `verify` job command set, including Python unit tests and focused shell tests, plus the new README and repository-structure thesis verifier and fixture test.
- Review-thread follow-up: CodeRabbit correctly flagged that the new control-plane-thesis verifier existed but was not called from CI; the workflow now includes both the verifier and its focused shell test.
- Keep this section short. The supervisor may compact older notes automatically.
