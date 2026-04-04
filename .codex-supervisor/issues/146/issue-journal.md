# Issue #146: design: define the control-plane MVP record model for alerts, cases, approvals, hunts, and AI traces

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/146
- Branch: codex/issue-146
- Workspace: .
- Journal: .codex-supervisor/issues/146/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 1363a7266522621a4f3f076db8d427ea3bff7c38
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T00:22:20.192Z

## Latest Codex Summary
- Tightened the control-plane state model verifier to require the Phase 7 MVP record families and explicit hunt/AI-trace reconciliation semantics, reproduced the gap against the pre-edit document, then updated the model doc so the focused checks now pass.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: `docs/control-plane-state-model.md` was too narrow for issue #146 because it omitted `Evidence`, `Hunt`, `Hunt Run`, and `AI Trace`, and the existing verifier did not assert those requirements.
- What changed: Expanded the model doc with the missing record families, explicit minimum reconciliation keys, hunt lifecycle expectations, hunt-run reconciliation expectations, and AI trace review/linkage expectations. Tightened `scripts/verify-control-plane-state-model-doc.sh` to enforce those statements.
- Current blocker: none
- Next exact step: Commit the verified documentation and journal updates on `codex/issue-146`.
- Verification gap: No gap in the required focused checks; broader review is still limited to documentation verification only.
- Files touched: `docs/control-plane-state-model.md`; `scripts/verify-control-plane-state-model-doc.sh`; `.codex-supervisor/issues/146/issue-journal.md`
- Rollback concern: Low; changes are documentation and verification-only, but reverting the script without the doc would re-open the acceptance gap.
- Last focused command: `bash scripts/verify-control-plane-state-model-doc.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
