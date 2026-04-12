# Issue #397: implementation: add bounded operator actions for case promotion, triage annotations, disposition, and handoff

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/397
- Branch: codex/issue-397
- Workspace: .
- Journal: .codex-supervisor/issues/397/issue-journal.md
- Current phase: addressing_review
- Attempt count: 3 (implementation=2, repair=1)
- Last head SHA: 4268156614001516a59ddc673538e84ccc839983
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc56VJHY|PRRT_kwDOR2iDUc56VJHa|PRRT_kwDOR2iDUc56VJHc|PRRT_kwDOR2iDUc56VJHd|PRRT_kwDOR2iDUc56VJHe|PRRT_kwDOR2iDUc56VJHf
- Repeated failure signature count: 1
- Updated at: 2026-04-11T22:57:48.124Z

## Latest Codex Summary
Implemented the missing reviewed operator surface for Phase 19 casework on top of the existing service-layer methods. `control-plane/main.py` now exposes bounded CLI commands and matching runtime `POST /operator/*` endpoints for alert promotion, case observations, leads, recommendations, handoff notes, and disposition updates, with strict JSON/string/list/datetime validation before delegating into the control-plane service.

I added end-to-end CLI and HTTP tests in `control-plane/tests/test_cli_inspection.py` to prove the full promote-to-casework flow updates the case's reviewed context correctly. Verification passed, the changes are committed as `4268156` (`Expose bounded operator casework actions`), the branch is pushed, and PR [#402](https://github.com/TommyKammy/AegisOps/pull/402) is open.

Summary: Exposed bounded operator casework actions through the reviewed CLI/runtime surface, added end-to-end CLI/HTTP coverage, pushed `codex/issue-397`, and opened PR #402
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_cli_records_bounded_operator_casework_actions`; `python3 -m unittest control-plane.tests.test_cli_inspection.ControlPlaneCliInspectionTests.test_long_running_runtime_surface_records_bounded_operator_casework_actions`; `python3 -m unittest control-plane.tests.test_cli_inspection control-plane.tests.test_service_persistence`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
Next action: Address PR #402 follow-up review comments on operator auth, request-size handling, atomic case disposition updates, and journal wording, then rerun the focused operator-surface checks before pushing.
Failure signature: PRRT_kwDOR2iDUc56VJHY|PRRT_kwDOR2iDUc56VJHa|PRRT_kwDOR2iDUc56VJHc|PRRT_kwDOR2iDUc56VJHd|PRRT_kwDOR2iDUc56VJHe|PRRT_kwDOR2iDUc56VJHf

## Active Failure Context
- Category: review
- Summary: 6 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/402#discussion_r3068705305
- Details:
  - .codex-supervisor/issues/397/issue-journal.md:19 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Clarify awkward phrasing in the summary sentence.** Line 19 reads as a broken compound phrase (“case reviewed context”). url=https://github.com/TommyKammy/AegisOps/pull/402#discussion_r3068705305
  - .codex-supervisor/issues/397/issue-journal.md:30 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Update stale “Next action” note to match current state.** Line 30 suggests deciding whether to expose bounded writes beyond the service layer... url=https://github.com/TommyKammy/AegisOps/pull/402#discussion_r3068705309
  - control-plane/aegisops_control_plane/service.py:2184 summary=_⚠️ Potential issue_ | _🟠 Major_ **Wrap multi-record updates in a transaction for atomicity.** This method persists the case record and conditionally persists the alert record ... url=https://github.com/TommyKammy/AegisOps/pull/402#discussion_r3068705311
  - control-plane/main.py:103 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Differentiate oversized bodies from malformed JSON.** `_read_json_request_body()` raises `ValueError` for size overruns, and every `/operator... url=https://github.com/TommyKammy/AegisOps/pull/402#discussion_r3068705312
  - control-plane/main.py:620 summary=_⚠️ Potential issue_ | _🔴 Critical_ **Protect `/operator/*` before shipping it.** These handlers are anonymous write APIs right now. url=https://github.com/TommyKammy/AegisOps/pull/402#discussion_r3068705313

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining Phase 19 gap was not in the service layer anymore; it was the reviewed operator surface itself. Operators could inspect alert and case detail, but could not yet promote alerts or record bounded casework actions through the CLI/runtime surface.
- What changed: Added explicit bounded operator commands and HTTP endpoints in `control-plane/main.py` for `promote-alert-to-case`, `record-case-observation`, `record-case-lead`, `record-case-recommendation`, `record-case-handoff`, and `record-case-disposition`. The runtime now accepts JSON POSTs for the same bounded actions under `/operator/*`, with strict string/list/datetime validation before delegating into the already-bounded service methods. Added focused CLI and HTTP tests that exercise the full promote-to-casework flow and verify the resulting reviewed case-detail state.
- Current blocker: CodeRabbit follow-up comments on operator-surface hardening and journal wording.
- Next exact step: Finish the operator-surface review fixes, rerun the focused CLI/runtime checks, commit the repair on `codex/issue-397`, and push PR #402 for another review pass.
- Verification gap: none for the implemented slice; the focused operator-surface tests passed and the full `control-plane/tests` discovery sweep passed.
- Files touched: control-plane/main.py; control-plane/tests/test_cli_inspection.py
- Rollback concern: The new write surface intentionally mirrors current service semantics, so any future schema change to case triage or handoff metadata will require corresponding CLI/HTTP payload reshaping.
- Last focused command: python3 -m unittest discover -s control-plane/tests -p 'test_*.py'
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
