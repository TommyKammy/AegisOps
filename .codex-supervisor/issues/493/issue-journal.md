# Issue #493: implementation: add a live approval-decision grant/reject HTTP path with approver-policy enforcement

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/493
- Branch: codex/issue-493
- Workspace: .
- Journal: .codex-supervisor/issues/493/issue-journal.md
- Current phase: local_review_fix
- Attempt count: 3 (implementation=1, repair=2)
- Last head SHA: 58bad0136f60b47c761f071eee00c9894f073095
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-16T03:50:08.637Z

## Latest Codex Summary
Restricted the live approval-decision surface to actual approvers in [http_surface.py](control-plane/aegisops_control_plane/http_surface.py:641), so `POST /operator/record-action-approval-decision` now fails closed unless the authenticated principal has role `approver`. That closes the local-review finding that an authenticated `analyst` could previously record a live grant/reject by supplying their own identity. I committed the code change as `58bad01` (`Restrict approval decisions to approvers`).

Added focused regression coverage in [test_phase23_approval_surface_validation.py](control-plane/tests/test_phase23_approval_surface_validation.py:41) so the runtime harness can run under alternate principals and now verifies an authenticated reviewed-reverse-proxy `analyst` gets `403` and leaves the request pending. I also updated the local issue journal working notes for the repair pass.

Summary: Restricted the live approval-decision HTTP route to `approver` principals only, added an analyst-`403` regression test, verified both focused suites, and committed the repair as `58bad01`.
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase23_approval_surface_validation`; `python3 -m unittest control-plane.tests.test_service_persistence_action_reconciliation`
Next action: Run a fresh local review on `58bad01`, or perform the pending manual operator-path validation if the supervisor wants runtime confirmation before re-review.
Failure signature: none

## Active Failure Context
- Category: blocked
- Summary: Local review found 3 actionable finding(s) across 3 root cause(s); max severity=high; verified high-severity findings=3; verified max severity=high.
- Details:
  - findings=3
  - root_causes=3
  - summary=<redacted-local-path>

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining blocked review findings were the missing PostgreSQL persistence contract for `ApprovalDecisionRecord.decision_rationale` and missing decision-time approver-policy enforcement inside `record_action_approval_decision(...)`.
- What changed: Added request-side approver-policy revalidation in `control-plane/aegisops_control_plane/service.py` so live approval decisions now fail closed unless the reviewed action class is still the supported `notify` class and any request-specific `policy_evaluation.authorized_approver_identities` allowlist includes the current approver. Added the missing `decision_rationale` column to `postgres/control-plane/schema.sql`, the bootstrap schema migration `0001_control_plane_schema_skeleton.sql`, and a new forward migration `0005_phase_23_approval_decision_rationale.sql`. Extended `control-plane/tests/test_phase23_approval_surface_validation.py` with a reviewed runtime regression that an `approver` outside the request allowlist receives `403`, and added `control-plane/tests/test_postgres_store.py` coverage that the forward migration asset and checked-in schema both carry the new column.
- Current blocker: none
- Next exact step: Commit the persistence plus approver-policy repair on `codex/issue-493`, then hand the branch back for a fresh local review or any requested manual operator-path validation.
- Verification gap: Manual end-to-end operator-path validation is still not run; automated coverage now includes live grant/reject, self-approval denial, analyst-role denial, request-specific approver-policy denial, the action-reconciliation persistence suite, and the PostgreSQL schema/migration asset checks.
- Files touched: control-plane/aegisops_control_plane/service.py; control-plane/tests/test_phase23_approval_surface_validation.py; control-plane/tests/test_postgres_store.py; postgres/control-plane/schema.sql; postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql; postgres/control-plane/migrations/0005_phase_23_approval_decision_rationale.sql; .codex-supervisor/issues/493/issue-journal.md
- Rollback concern: `ApprovalDecisionRecord` now includes persisted `decision_rationale`; rollback must account for any rows serialized with the new field in stores used during verification.
- Last focused commands: `python3 -m unittest control-plane.tests.test_phase23_approval_surface_validation`; `python3 -m unittest control-plane.tests.test_service_persistence_action_reconciliation`; `python3 -m unittest control-plane.tests.test_postgres_store`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
