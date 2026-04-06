# Issue #246: design: define the Wazuh alert-ingest contract and mapping into Analytic Signal

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/246
- Branch: codex/issue-246
- Workspace: .
- Journal: .codex-supervisor/issues/246/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 6a7b0a8a55f51a4f52d35619071b0eb6bffe48c3
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-06T14:08:35.368Z

## Latest Codex Summary
- Added a focused documentation unittest that reproduced the missing Wazuh ingest-contract gap, then added `docs/wazuh-alert-ingest-contract.md` plus cross-links from the state-model and secops-domain docs.
- Verified the new contract against the focused unittest and the issue-specified `rg` query.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The issue was a reviewed-documentation gap rather than a runtime bug; the repo had generic analytic-signal semantics but no Wazuh-specific intake contract that fixed required fields, provenance, and identifier mapping into first-class analytic signals.
- What changed: Added `control-plane/tests/test_wazuh_alert_ingest_contract_docs.py` to reproduce the gap, created `docs/wazuh-alert-ingest-contract.md`, and cross-linked it from `docs/secops-domain-model.md` and `docs/control-plane-state-model.md`.
- Current blocker: none
- Next exact step: Stage the docs and focused test, commit the checkpoint, and leave the branch ready for local review or draft PR creation.
- Verification gap: Focused docs verification passed; broader review is still manual and no broader automated doc lint suite exists in this repo.
- Files touched: `.codex-supervisor/issues/246/issue-journal.md`, `control-plane/tests/test_wazuh_alert_ingest_contract_docs.py`, `docs/wazuh-alert-ingest-contract.md`, `docs/secops-domain-model.md`, `docs/control-plane-state-model.md`
- Rollback concern: Low; changes are additive documentation plus a narrow unittest asserting the contract file and cross-links exist.
- Last focused command: `rg -n "Wazuh|Analytic Signal|substrate_detection_record_id|analytic_signal_id|alert_id" docs control-plane`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
