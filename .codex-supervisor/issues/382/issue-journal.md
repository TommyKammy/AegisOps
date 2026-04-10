# Issue #382: validation: add end-to-end Phase 18 coverage for live Wazuh alert intake into the AegisOps analyst queue

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/382
- Branch: codex/issue-382
- Workspace: .
- Journal: .codex-supervisor/issues/382/issue-journal.md
- Current phase: stabilizing
- Attempt count: 2 (implementation=2, repair=0)
- Last head SHA: f4c3993b11fbe06fc9bd68db9901be0f0bc7230b
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T23:21:46.107Z

## Latest Codex Summary
Added a dedicated Phase 18 repository-local validator for the live Wazuh webhook path into the analyst queue. The new test drives authenticated `ingest_wazuh_alert` delivery for the approved `github_audit` family through `created`, `restated`, and `deduplicated` outcomes, then asserts the queue still exposes a single Wazuh-origin record with preserved case linkage, merged substrate IDs, live admission provenance, and the expected business-hours routing.

I also wired that validator into the existing Phase 18 validation record and shell verifier so the slice fails closed if the live queue coverage disappears. The checkpoint is committed on `codex/issue-382` as `f4c3993` with message `Add Phase 18 live Wazuh queue validation`.

Summary: Added Phase 18 end-to-end live Wazuh queue validation and verifier coverage; committed as `f4c3993`
State hint: implementing
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase18_live_wazuh_queue_validation`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
Next action: Open or update a draft PR for the committed Phase 18 validation slice if supervisor flow wants an early checkpoint published
Failure signature: none

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The missing Phase 18 coverage was a dedicated repository-local validator for the reviewed live Wazuh webhook path into the analyst queue, not a broad service bug.
- What changed: Added `control-plane/tests/test_phase18_live_wazuh_queue_validation.py`; updated `docs/phase-18-wazuh-lab-topology-validation.md`; extended `scripts/verify-phase-18-wazuh-lab-topology.sh` and `scripts/test-verify-phase-18-wazuh-lab-topology.sh` to require the new validator.
- Current blocker: none
- Next exact step: Monitor draft PR `#387` for review or CI feedback and address only focused validation regressions if they appear.
- Verification gap: none for the requested repository-local validation slice; broader Phase 19 operator-surface coverage remains intentionally out of scope.
- Files touched: `.codex-supervisor/issues/382/issue-journal.md`, `control-plane/tests/test_phase18_live_wazuh_queue_validation.py`, `docs/phase-18-wazuh-lab-topology-validation.md`, `scripts/verify-phase-18-wazuh-lab-topology.sh`, `scripts/test-verify-phase-18-wazuh-lab-topology.sh`
- Rollback concern: Low; changes are additive validation/doc/verifier updates and do not alter runtime service logic.
- Last focused commands: `python3 -m unittest control-plane.tests.test_phase18_live_wazuh_queue_validation`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Focused reproducer note: the first draft of the new test intentionally changed `data.request_id`, which exercised `updated` reviewed-context behavior instead of `restated`; the final test now changes only native id/timestamp to isolate repeat live-delivery semantics.
- Stabilization note: Re-ran the dedicated Phase 18 validator, both shell verifier paths, and the full `control-plane/tests` unittest discovery sweep on 2026-04-11; all passed without additional code changes.
- Publish note: Pushed `codex/issue-382` and opened draft PR `#387` (`[codex] Add Phase 18 live Wazuh queue validation`) against `main`.
