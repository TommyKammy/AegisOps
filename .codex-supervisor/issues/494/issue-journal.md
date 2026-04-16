# Issue #494: implementation: add append-only lifecycle transition logging beside current-state records

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/494
- Branch: codex/issue-494
- Workspace: .
- Journal: .codex-supervisor/issues/494/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 33 (implementation=1, repair=1)
- Last head SHA: bd2f544a9401d8e55c2114c455cfcb387cee5589
- Blocked reason: none
- Last failure signature: local-review:high:high:4:1:clean
- Repeated failure signature count: 2
- Updated at: 2026-04-16T14:11:06.000Z

## Latest Codex Summary
Committed `bd2f544` on `codex/issue-494` with the saved local-review repair set. The service now rejects explicit lifecycle timestamps that would backdate a transition behind newer history while preserving equal reviewed timestamps with deterministic same-time transition IDs, the PostgreSQL adapter maps lifecycle rows before cursor close, and the first-boot entrypoint normalizes CRLF/LF differences before recording reviewed migration checksums.

I also added regression coverage for the timestamp, tuple-row cursor, and CRLF bootstrap cases, then reran the focused transition, restore, persistence, bootstrap, advisory, reconciliation, and CLI suites cleanly. The remaining step is to push the repaired head and refresh local review / PR `#501` on `bd2f544a9401d8e55c2114c455cfcb387cee5589`.

Summary: Committed `bd2f544` with the four saved local-review repairs plus regression coverage; a fresh local review is still pending.
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase23_transition_logging_validation`; `python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness`; `python3 -m unittest control-plane.tests.test_postgres_store`; `python3 -m unittest control-plane.tests.test_phase16_bootstrap_contract_docs`; `python3 -m unittest control-plane.tests.test_service_persistence_action_reconciliation`; `python3 -m unittest control-plane.tests.test_service_persistence_assistant_advisory`; `python3 -m unittest control-plane.tests.test_cli_inspection`
Next action: Push `bd2f544a9401d8e55c2114c455cfcb387cee5589` to `codex/issue-494` and refresh local review / PR `#501` status on the repaired head.
Failure signature: none

## Active Failure Context
- Category: review
- Summary: Saved local-review repair pass completed on `bd2f544a9401d8e55c2114c455cfcb387cee5589`; all four recorded root causes were addressed locally and now need a fresh review verdict.
- Details:
  - repaired_findings=4
  - repaired_root_causes=4
  - reviewed_head_sha=bd2f544a9401d8e55c2114c455cfcb387cee5589
  - prior_summary=<redacted-local-path>

## Codex Working Notes
### Current Handoff
- Hypothesis: The saved local-review findings should clear on a fresh pass because the repaired head now covers the explicit timestamp backfill bug, the cursor-close row-mapping bug, the CRLF-sensitive migration checksum bug, and the stale journal state mismatch.
- What changed: `control-plane/aegisops_control_plane/service.py` now preserves equal explicit timestamps with ordered transition IDs and rejects explicit historical backfills; `control-plane/aegisops_control_plane/adapters/postgres.py` maps lifecycle rows before `close()`; `control-plane/deployment/first-boot/control-plane-entrypoint.sh` normalizes CRLF/LF before checksuming migrations; `control-plane/tests/support/service_persistence.py`, `control-plane/tests/test_cli_inspection.py`, `control-plane/tests/test_phase16_bootstrap_contract_docs.py`, `control-plane/tests/test_phase23_transition_logging_validation.py`, and `control-plane/tests/test_postgres_store.py` now cover the repaired behavior.
- Current blocker: none.
- Next exact step: Push `bd2f544a9401d8e55c2114c455cfcb387cee5589`, then rerun local review / inspect PR `#501` on that head.
- Verification gap: No known failing local suites remain in the touched paths; the remaining gap is a fresh local review verdict on `bd2f544a9401d8e55c2114c455cfcb387cee5589`.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/aegisops_control_plane/adapters/postgres.py`, `control-plane/deployment/first-boot/control-plane-entrypoint.sh`, `control-plane/tests/support/service_persistence.py`, `control-plane/tests/test_cli_inspection.py`, `control-plane/tests/test_phase16_bootstrap_contract_docs.py`, `control-plane/tests/test_phase23_transition_logging_validation.py`, `control-plane/tests/test_postgres_store.py`, and `.codex-supervisor/issues/494/issue-journal.md`.
- Rollback concern: Rolling back would reintroduce silent lifecycle timestamp restamping, driver-dependent lifecycle reads after cursor close, and CRLF-sensitive reviewed migration checksum drift on first boot.
- Last focused command: `python3 -m unittest control-plane.tests.test_phase23_transition_logging_validation`, `python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness`, `python3 -m unittest control-plane.tests.test_postgres_store`, `python3 -m unittest control-plane.tests.test_phase16_bootstrap_contract_docs`, `python3 -m unittest control-plane.tests.test_service_persistence_action_reconciliation`, `python3 -m unittest control-plane.tests.test_service_persistence_assistant_advisory`, `python3 -m unittest control-plane.tests.test_cli_inspection`, `git commit -m "Fix lifecycle transition review defects"`, and `git rev-parse HEAD`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Current local focus: push the repaired head and confirm the saved local-review findings clear on a fresh pass.
- New local regressions: none observed in the touched suites after the repair set landed.
- Review baseline under repair: the four saved findings in `service.py`, `adapters/postgres.py`, `control-plane-entrypoint.sh`, and the tracked supervisor journal state.
