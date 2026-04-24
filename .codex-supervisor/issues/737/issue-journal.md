# Issue #737: operations: add the reviewed upgrade procedure needed to fully close Phase 32

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/737
- Branch: codex/issue-737
- Workspace: .
- Journal: .codex-supervisor/issues/737/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: d6c612a7f2b6304f1fdbec1c3708cd2e8d384291
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-24T03:54:40.983Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 32 was still open because `docs/runbook.md` had backup, restore, rollback, and secret-rotation contracts but no explicit reviewed upgrade contract or verifier coverage for it.
- What changed: Added a reviewed upgrade procedure to `docs/runbook.md` with upgrade preconditions, ordered steps, post-upgrade checks, rollback trigger, evidence retention, and SMB-baseline alignment; added focused Phase 32 unittest coverage; tightened `scripts/verify-runbook-doc.sh`; and updated `scripts/test-verify-runbook-doc.sh` so the verifier self-test includes the upgrade contract.
- Current blocker: none
- Next exact step: Stage the runbook and verifier changes, commit the checkpoint on `codex/issue-737`, and leave the branch ready for PR creation or supervisor pickup.
- Verification gap: none for the doc-contract slice covered here; broader runtime upgrade execution remains intentionally out of scope for this issue.
- Files touched: docs/runbook.md; control-plane/tests/test_phase32_secret_rotation_runbook_docs.py; scripts/verify-runbook-doc.sh; scripts/test-verify-runbook-doc.sh
- Rollback concern: The runbook now requires same-day rollback readiness and evidence retention for upgrades; reverting this change would reopen the documented Phase 32 gap.
- Last focused command: node /Users/jp.infra/Dev/codex-supervisor/dist/index.js issue-lint 737 --config /Users/jp.infra/Dev/codex-supervisor/supervisor.config.aegisops.coderabbit.json
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
