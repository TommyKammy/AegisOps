# Issue #382: validation: add end-to-end Phase 18 coverage for live Wazuh alert intake into the AegisOps analyst queue

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/382
- Branch: codex/issue-382
- Workspace: .
- Journal: .codex-supervisor/issues/382/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 8e3d883d74368ff33ca98443cfda7e689c2b9502
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T23:14:07.507Z

## Latest Codex Summary
- Added repository-local Phase 18 validation for authenticated live `ingest_wazuh_alert` delivery into the analyst queue, covering GitHub audit admission, repeat live delivery restatement/deduplication, and preserved case linkage.
- Extended the Phase 18 validation record and shell verifier so the new live queue validator is required alongside the existing topology and asset guards.
- Verified with the focused Phase 18 unit test, the Phase 18 shell verifier and self-test, and full `control-plane/tests` discovery.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The missing Phase 18 coverage was a dedicated repository-local validator for the reviewed live Wazuh webhook path into the analyst queue, not a broad service bug.
- What changed: Added `control-plane/tests/test_phase18_live_wazuh_queue_validation.py`; updated `docs/phase-18-wazuh-lab-topology-validation.md`; extended `scripts/verify-phase-18-wazuh-lab-topology.sh` and `scripts/test-verify-phase-18-wazuh-lab-topology.sh` to require the new validator.
- Current blocker: none
- Next exact step: Commit the Phase 18 validation slice on `codex/issue-382`.
- Verification gap: none for the requested repository-local validation slice; broader Phase 19 operator-surface coverage remains intentionally out of scope.
- Files touched: `.codex-supervisor/issues/382/issue-journal.md`, `control-plane/tests/test_phase18_live_wazuh_queue_validation.py`, `docs/phase-18-wazuh-lab-topology-validation.md`, `scripts/verify-phase-18-wazuh-lab-topology.sh`, `scripts/test-verify-phase-18-wazuh-lab-topology.sh`
- Rollback concern: Low; changes are additive validation/doc/verifier updates and do not alter runtime service logic.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Focused reproducer note: the first draft of the new test intentionally changed `data.request_id`, which exercised `updated` reviewed-context behavior instead of `restated`; the final test now changes only native id/timestamp to isolate repeat live-delivery semantics.
