# Issue #209: documentation: mark OpenSearch, Sigma, and n8n assets as transitional or optional in README and repository baseline

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/209
- Branch: codex/issue-209
- Workspace: .
- Journal: .codex-supervisor/issues/209/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: ff2b7b6fdbb884a33037740aeee78e8034942f2f
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-06T01:41:00.649Z

## Latest Codex Summary
- Reproduced the mismatch with a focused README/repository-structure verifier, updated both docs to the approved control-plane thesis, and added a regression test plus verifier for future checks.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: `README.md` and `docs/repository-structure-baseline.md` still describe the older OpenSearch + Sigma + n8n-centered thesis instead of the approved governed control-plane thesis from ADR-0002 and `docs/architecture.md`.
- What changed: Added `scripts/verify-readme-and-repository-structure-control-plane-thesis.sh` plus its fixture test, then rewrote the README introduction, component summaries, architecture overview, and repository-structure framing to mark OpenSearch, Sigma, and n8n as optional or transitional and to mark the current top-level tree as transitional pending a later ADR.
- Current blocker: none
- Next exact step: Stage the doc and verifier changes, create a checkpoint commit on `codex/issue-209`, and decide whether to open a draft PR.
- Verification gap: No broader CI run yet; focused doc verification and targeted grep checks are green.
- Files touched: README.md; docs/repository-structure-baseline.md; scripts/verify-readme-and-repository-structure-control-plane-thesis.sh; scripts/test-verify-readme-and-repository-structure-control-plane-thesis.sh; .codex-supervisor/issues/209/issue-journal.md
- Rollback concern: Low; changes are documentation and doc-verifier only, with no repository tree or runtime behavior changes.
- Last focused command: bash scripts/verify-readme-and-repository-structure-control-plane-thesis.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
