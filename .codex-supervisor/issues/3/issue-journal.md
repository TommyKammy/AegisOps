# Issue #3: design: define AegisOps naming conventions for hosts, compose projects, indexes, and workflows

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/3
- Branch: codex/issue-3
- Workspace: .
- Journal: .codex-supervisor/issues/3/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 832a445f7b047915d2b2e7c3c09b509c6d5c60ad
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-01T05:04:44.550Z

## Latest Codex Summary
- Added a focused naming-conventions verifier, used it to reproduce a missing hostname naming section in `docs/requirements-baseline.md`, then expanded section 7 to cover hostnames, compose projects, OpenSearch indexes, detectors, n8n workflows, and secrets/environment variables with explicit examples.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue #3 is satisfied by tightening the baseline naming section and adding a narrow verifier that proves all required naming categories and examples exist without introducing runtime changes.
- What changed: Added `scripts/verify-naming-conventions-doc.sh`; updated `docs/requirements-baseline.md` section 7 with explicit hostname naming rules, renamed and expanded compose/index/detector/workflow/secret subsections, and added concrete AegisOps examples.
- Current blocker: none
- Next exact step: Commit the documentation and verifier changes, then report the focused verification results.
- Verification gap: No broader markdown lint or repository-wide doc validation exists in this workspace; focused naming and repository-structure checks passed.
- Files touched: `docs/requirements-baseline.md`, `scripts/verify-naming-conventions-doc.sh`
- Rollback concern: low; documentation and verification-script only.
- Last focused command: `scripts/verify-naming-conventions-doc.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
