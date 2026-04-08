# Issue #321: implementation: add analyst-assistant query surfaces over control-plane records, reviewed context, and linked evidence

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/321
- Branch: codex/issue-321
- Workspace: .
- Journal: .codex-supervisor/issues/321/issue-journal.md
- Current phase: addressing_review
- Attempt count: 2 (implementation=1, repair=1)
- Last head SHA: 13dd7de2fb1e6ec239ca7af34e0bcd694d08404a
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc55tet4|PRRT_kwDOR2iDUc55tet6
- Repeated failure signature count: 1
- Updated at: 2026-04-08T23:55:09Z

## Latest Codex Summary
Implemented the new read-only analyst-assistant context surface in [service.py](control-plane/aegisops_control_plane/service.py#L150) and [main.py](control-plane/main.py#L45). It now returns the primary control-plane record plus reviewed context and linked evidence/recommendation/reconciliation citations, and it’s covered by focused tests in [test_service_persistence.py](control-plane/tests/test_service_persistence.py#L257) and [test_cli_inspection.py](control-plane/tests/test_cli_inspection.py#L223). I also updated [README.md](control-plane/README.md#L15) and opened draft PR `#327`.

Summary: Added `inspect-assistant-context` for citation-first analyst-assistant queries over reviewed control-plane state and linked evidence, with review-thread fixes for action-request linkage and missing evidence preservation.
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection`
Next action: Commit and push the review fixes to update PR `#327`, then confirm the review threads close out
Failure signature: PRRT_kwDOR2iDUc55tet4|PRRT_kwDOR2iDUc55tet6

## Active Failure Context
- Category: review
- Summary: 2 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/327#discussion_r3054782944
- Details:
  - control-plane/aegisops_control_plane/service.py:751 summary=_⚠️ Potential issue_ | _🟠 Major_ **Resolve approval/execution context through `action_request_id`.** This linkage builder only uses direct `alert_id` / `case_id` / `finding_id`... url=https://github.com/TommyKammy/AegisOps/pull/327#discussion_r3054782944
  - control-plane/aegisops_control_plane/service.py:763 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Preserve declared evidence IDs even when a linked record is missing.** `linked_evidence_ids` gets overwritten with only the evidence rows tha... url=https://github.com/TommyKammy/AegisOps/pull/327#discussion_r3054782946

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 15 needed a citation-oriented assistant context query surface because generic record listing did not explicitly join reviewed context with linked evidence.
- What changed: Added `AnalystAssistantContextSnapshot`, `AegisOpsControlPlaneService.inspect_assistant_context()`, and the `inspect-assistant-context` CLI command; then repaired assistant-context linkage so approval/execution records resolve through `ActionRequestRecord` and declared evidence IDs are preserved even when some records are missing.
- Current blocker: None.
- Next exact step: Commit the review fix, push branch `codex/issue-321`, and let PR `#327` re-run review/CI.
- Verification gap: None for the issue-specified control-plane persistence and CLI inspection suite; focused unittest slice passed after the fix.
- Files touched: `control-plane/aegisops_control_plane/service.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/main.py`, `control-plane/aegisops_control_plane/__init__.py`, `control-plane/tests/test_cli_inspection.py`, `control-plane/README.md`.
- Rollback concern: The new assistant-context surface is additive and read-only; reverting the new CLI command and service method restores the prior inspection-only surface.
- Last focused command: `python3 -m unittest control-plane.tests.test_service_persistence control-plane.tests.test_cli_inspection`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
