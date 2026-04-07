# Issue #283: Follow-up: Follow-up: design: define the approved automation substrate contract and approval-binding model (#266) - The new delegation contract makes `Action Execution` an AegisOps-owned record by stating that execution-surface receipts ...

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/283
- Branch: codex/issue-283
- Workspace: .
- Journal: .codex-supervisor/issues/283/issue-journal.md
- Current phase: repairing_ci
- Attempt count: 2 (implementation=1, repair=1)
- Last head SHA: fdc75fa692e85df7f7c7ce94e3de6539862f16aa
- Blocked reason: none
- Last failure signature: verify:fail
- Repeated failure signature count: 1
- Updated at: 2026-04-07T12:32:48.028Z

## Latest Codex Summary
Updated the residual spec gap by adding a normative `Action Execution` subsection to [docs/control-plane-state-model.md](docs/control-plane-state-model.md) and tightening the focused shared-doc guardrail in [control-plane/tests/test_wazuh_alert_ingest_contract_docs.py](control-plane/tests/test_wazuh_alert_ingest_contract_docs.py). The new section now defines minimum `action_execution_id` lineage fields, execution-surface correlation fields, payload/idempotency binding, and explicit lifecycle states aligned to the delegation contract from PR #281.

I reproduced the issue first with the new test, then fixed it and re-ran the focused verification. I also updated the issue journal at [.codex-supervisor/issues/283/issue-journal.md](.codex-supervisor/issues/283/issue-journal.md), committed the change as `fdc75fa`, pushed `codex/issue-283`, and opened draft PR #290: `https://github.com/TommyKammy/AegisOps/pull/290`.

Summary: Added the missing normative `Action Execution` state-model contract, added a focused regression test for it, committed, pushed, and opened draft PR #290.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_wazuh_alert_ingest_contract_docs`
Next action: Move from draft PR review into any requested follow-up wording or broader validation if reviewers want additional guardrails.
Failure signature: verify:fail

## Active Failure Context
- Category: checks
- Summary: PR #290 has failing checks.
- Command or source: gh pr checks
- Reference: https://github.com/TommyKammy/AegisOps/pull/290
- Details:
  - verify (fail/FAILURE) https://github.com/TommyKammy/AegisOps/actions/runs/24081232401/job/70242105003

## Codex Working Notes
### Current Handoff
- Hypothesis: The GitHub `verify` failure on PR #290 is a stale guardrail, not a remaining spec gap: `scripts/verify-control-plane-state-model-doc.sh` still required the pre-follow-up lifecycle sentence that omitted `Action Execution`, so `scripts/verify-phase-10-thesis-consistency.sh` failed even though `docs/control-plane-state-model.md` had already been updated.
- What changed: Updated `scripts/verify-control-plane-state-model-doc.sh` to require the corrected lifecycle-contract sentence including `Action Execution`, and added a direct regression case in `scripts/test-verify-control-plane-state-model-doc.sh` that fails closed if that sentence is removed again.
- Current blocker: none
- Next exact step: Commit and push the verifier repair on `codex/issue-283`, then monitor PR #290 for a fresh `verify` rerun on the new head.
- Verification gap: Focused local reproduction and regression coverage now include the exact failing thesis verifier plus the earlier `Action Execution` unittest; broader suite coverage still is not required for this docs-and-verifier repair.
- Files touched: `.codex-supervisor/issues/283/issue-journal.md`, `docs/control-plane-state-model.md`, `control-plane/tests/test_wazuh_alert_ingest_contract_docs.py`, `scripts/verify-control-plane-state-model-doc.sh`, `scripts/test-verify-control-plane-state-model-doc.sh`
- Rollback concern: Low; the repair only aligns a stale string-based guardrail and adds a narrow regression case for the approved `Action Execution` lifecycle contract.
- Last focused commands: `python3 <redacted-local-path> --repo . --pr 290 --json`; `bash scripts/verify-phase-10-thesis-consistency.sh`; `bash scripts/test-verify-control-plane-state-model-doc.sh`; `python3 -m unittest control-plane.tests.test_wazuh_alert_ingest_contract_docs`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
