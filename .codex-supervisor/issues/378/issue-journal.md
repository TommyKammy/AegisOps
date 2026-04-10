# Issue #378: design: define the Phase 18 Wazuh lab topology, first live source family, and live ingest contract

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/378
- Branch: codex/issue-378
- Workspace: .
- Journal: .codex-supervisor/issues/378/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 87af17f9b140424545b1680f6a02d9bb1626d024
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-10T13:34:25.777Z

## Latest Codex Summary
- Added a focused Phase 18 doc test to reproduce the missing-artifact failure, then defined the Phase 18 Wazuh lab topology, first live source family, validation record, and verifier scripts around one narrow `Wazuh -> AegisOps` live path.

## Active Failure Context
- Reproduced initial failure: `python3 -m unittest control-plane.tests.test_phase18_wazuh_lab_topology_docs` failed because `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md` and `docs/phase-18-wazuh-lab-topology-validation.md` did not exist.

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 18 needed the same artifact pattern as prior phases: focused doc guard, design doc, validation record, and shell verifier anchored to the Phase 16/17 boot boundary and existing Wazuh/source-family contracts.
- What changed: Added `control-plane/tests/test_phase18_wazuh_lab_topology_docs.py`; added `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md` and `docs/phase-18-wazuh-lab-topology-validation.md`; added `scripts/verify-phase-18-wazuh-lab-topology.sh` and `scripts/test-verify-phase-18-wazuh-lab-topology.sh`; updated `README.md` and `docs/documentation-ownership-map.md` to reference the new Phase 18 artifacts.
- Current blocker: none
- Next exact step: commit the coherent Phase 18 docs/test/verifier checkpoint on `codex/issue-378`.
- Verification gap: focused Phase 18 checks passed; no broader suite run because this slice is documentation/verifier scoped.
- Files touched: `control-plane/tests/test_phase18_wazuh_lab_topology_docs.py`, `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md`, `docs/phase-18-wazuh-lab-topology-validation.md`, `scripts/verify-phase-18-wazuh-lab-topology.sh`, `scripts/test-verify-phase-18-wazuh-lab-topology.sh`, `README.md`, `docs/documentation-ownership-map.md`
- Rollback concern: low; changes are additive documentation and focused verification only.
- Last focused command: `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
