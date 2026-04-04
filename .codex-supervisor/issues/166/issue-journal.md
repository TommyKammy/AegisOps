# Issue #166: design: define the finding-to-alert ingestion and reconciliation contract for the control plane

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/166
- Branch: codex/issue-166
- Workspace: .
- Journal: .codex-supervisor/issues/166/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 3027971aa02d483b1c87624088c460d4828d5624
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T09:27:05.036Z

## Latest Codex Summary
- None yet.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The docs already mentioned identifiers, but the finding-to-alert ingestion contract and duplicate/restatement boundary were still too implicit for future ingest work.
- What changed: Tightened the two doc verification scripts with focused finding-to-alert contract assertions, fixed a verifier quoting bug caused by backticks in required phrases, and added explicit contract language to the control-plane and SecOps docs.
- Current blocker: none
- Next exact step: Commit the focused documentation and verification updates on `codex/issue-166`.
- Verification gap: No broader repo-wide verification run; only the issue-targeted grep and document verification scripts were exercised.
- Files touched: docs/control-plane-state-model.md; docs/secops-domain-model.md; scripts/verify-control-plane-state-model-doc.sh; scripts/verify-secops-domain-model-doc.sh
- Rollback concern: Low; changes are documentation plus doc-specific verification only.
- Last focused command: rg -n "finding_id|analytic_signal_id|alert_id|duplicate|restated|ingestion contract" docs/control-plane-state-model.md docs/secops-domain-model.md
### Scratchpad
- Reproduced gap by tightening verification first. Initial verifier patch failed because backticks in bash double-quoted array entries triggered command substitution; fixed by using single-quoted phrases before updating docs.
