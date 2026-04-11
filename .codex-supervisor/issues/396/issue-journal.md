# Issue #396: implementation: expose case detail, evidence provenance, reviewed context, and cited advisory output on the operator surface

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/396
- Branch: codex/issue-396
- Workspace: .
- Journal: .codex-supervisor/issues/396/issue-journal.md
- Current phase: addressing_review
- Attempt count: 3 (implementation=2, repair=1)
- Last head SHA: 692ecd504ccfa99de9ac0ac7e14ae255255d15ea
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc56VBjQ
- Repeated failure signature count: 1
- Updated at: 2026-04-11T22:21:52Z

## Latest Codex Summary
I validated the remaining unresolved CodeRabbit thread on [PR #401](https://github.com/TommyKammy/AegisOps/pull/401), confirmed that the new `inspect-case-detail` HTTP test still had a plain `request.urlopen(...)`, and added a narrow `# noqa: S310` annotation only on that new case-detail request.

Focused verification passed for `python3 -m unittest control-plane.tests.test_cli_inspection`. Ruff is not installed in the workspace interpreter, so I used `uvx ruff` for targeted inspection; whole-file `ruff check` still reports unrelated pre-existing `E402` and `S310` findings elsewhere in `control-plane/tests/test_cli_inspection.py`, but the review-thread line itself is now explicitly suppressed as intended.

Summary: Applied the local review fix for the unresolved `S310` thread on the new case-detail HTTP test call.
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_cli_inspection`; `python3 -m ruff check control-plane/tests/test_cli_inspection.py` (fails: module missing); `uv run ruff check control-plane/tests/test_cli_inspection.py` (fails: no local ruff binary); `uvx ruff check control-plane/tests/test_cli_inspection.py` (fails on unrelated pre-existing `E402`); `uvx ruff check --select S310 control-plane/tests/test_cli_inspection.py` (shows unrelated pre-existing `S310` outside the PR thread)
Next action: Commit and push the review-fix patch to PR #401, then leave the thread for reviewer/tool re-evaluation unless explicitly asked to reply or resolve it.
Failure signature: PRRT_kwDOR2iDUc56VBjQ

## Active Failure Context
- Category: review
- Summary: 1 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/401#discussion_r3068666281
- Details:
  - control-plane/tests/test_cli_inspection.py:284 summary=_⚠️ Potential issue_ | _🟠 Major_ **Address Ruff `S310` on the new case-detail HTTP call.** The new `urlopen` call in this changed block is currently flagged and can block CI li... url=https://github.com/TommyKammy/AegisOps/pull/401#discussion_r3068666281

## Codex Working Notes
### Current Handoff
- Hypothesis: Phase 19 operator coverage was missing a dedicated case-detail inspection path even though queue, alert detail, assistant context, and cited advisory views already existed.
- What changed: Added a failing CLI reproducer for `inspect-case-detail`, implemented `CaseDetailSnapshot` plus `inspect_case_detail()` by composing the existing reviewed assistant-context/advisory boundary, exposed the path in CLI and HTTP runtime routing, added HTTP coverage, updated the control-plane README command list, widened verification to the full control-plane unittest suite, pushed the branch, and opened draft PR #401.
- Current blocker: none
- Next exact step: Commit and push the local `S310` review fix for PR #401, then wait for GitHub review state to refresh.
- Verification gap: The review-fix change itself is covered by the CLI inspection test module; no clean whole-file Ruff baseline exists for `control-plane/tests/test_cli_inspection.py` because unrelated `E402` and `S310` findings predate this turn.
- Files touched: .codex-supervisor/issues/396/issue-journal.md; control-plane/aegisops_control_plane/service.py; control-plane/main.py; control-plane/tests/test_cli_inspection.py; control-plane/README.md
- Rollback concern: Low; the new path is read-only and reuses the existing assistant-context/advisory projections instead of introducing new mutable workflow behavior.
- Last focused command: uvx ruff check --select S310 control-plane/tests/test_cli_inspection.py
### Scratchpad
- Reproduced surface gap as argparse invalid choice for `inspect-case-detail`; resolved by adding a reviewed case-detail view that carries linked evidence provenance, reviewed context, and cited advisory output.
- Review follow-up: CodeRabbit thread `PRRT_kwDOR2iDUc56VBjQ` is valid for the newly added case-detail HTTP test call only; added a single-line `# noqa: S310` there and left unrelated pre-existing `urlopen` sites untouched to avoid broad behavior-neutral churn during review handling.
