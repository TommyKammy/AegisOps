# Issue #577: implementation: add bounded evidence-collection request path and artifact ingestion

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/577
- Branch: codex/issue-577
- Workspace: .
- Journal: .codex-supervisor/issues/577/issue-journal.md
- Current phase: addressing_review
- Attempt count: 3 (implementation=1, repair=2)
- Last head SHA: bc3b2209f3acd6567834fed68e70c5274738fb2d
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc57_jA1
- Repeated failure signature count: 3
- Updated at: 2026-04-19T05:06:43.333Z

## Latest Codex Summary
Implemented the review fixes on `codex/issue-577` and pushed `bc3b220` to PR #583. The service now creates endpoint-evidence requests under `SERIALIZABLE` with an idempotency advisory lock, uses valid action-policy enums, authorizes approval for the bounded read-only request type, admits artifacts only from `approved` or `executing` requests, and reuses existing `EvidenceRecord`s on retry instead of duplicating them. I also updated the Phase 28 tests to require approval before ingest, cover pending-approval rejection and retry idempotency, and remove the two lint nits CodeRabbit flagged.

Focused verification passed. `ruff` is not installed in this workspace, so a local Ruff run was not available.

Summary: Addressed the Phase 28 review threads with tighter request/approval/ingest boundaries, added retry-safe artifact reuse, updated focused tests, committed `bc3b220`, and pushed `codex/issue-577`.
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase28_endpoint_evidence_pack_validation`; `python3 -m unittest control-plane.tests.test_phase23_transition_logging_validation`; `python3 -m compileall control-plane/aegisops_control_plane/service.py control-plane/tests/test_phase28_endpoint_evidence_pack_validation.py`; `node <redacted-local-path> issue-lint 577 --config <redacted-local-path>`
Next action: re-check PR #583 review threads on the new head and resolve or answer the remaining automated comments if GitHub still shows any open against `bc3b220`.
Failure signature: PRRT_kwDOR2iDUc57_jA1

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: CodeRabbit's second-pass review on `bc3b220` found one real service-boundary gap and one real test-gap: artifact ingestion needed to enforce the request TTL in addition to lifecycle state, and the rollback stress test's mutation harness was arming itself during setup evidence writes instead of only during endpoint-artifact persistence.
- What changed: Tightened `ingest_endpoint_evidence_artifacts` to reject expired endpoint evidence requests even when their lifecycle state is still `approved`/`executing`, keeping the bounded approval window fail-closed at the ingestion boundary. Narrowed `_EvidenceSaveMutationStore.save()` so the mutation hook only fires for endpoint-evidence artifact records (`source_record_id` prefixed with `endpoint-evidence://request/`), which makes the unsupported-artifact rollback test exercise the intended write path instead of consuming the mutation during fixture setup. Added a focused Phase 28 regression test proving expired approved requests are rejected without durable evidence writes.
- Current blocker: none
- Next exact step: monitor PR #583 on pushed head `d7b101f` until the fresh `verify` run and CodeRabbit re-review complete, then inspect any remaining non-outdated threads.
- Verification gap: `ruff` is not installed in this workspace (`python3 -m ruff check ...` failed with `No module named ruff`), so verification is currently the focused unittest coverage plus `issue-lint`.
- Files touched: `control-plane/aegisops_control_plane/service.py`; `control-plane/tests/test_phase28_endpoint_evidence_pack_validation.py`; `.codex-supervisor/issues/577/issue-journal.md`
- Rollback concern: the new expiry guard is intentionally fail-closed at artifact admission time but does not currently persist an automatic `expired` lifecycle transition; if a future reviewer wants the action request record itself to age into `expired` here, that should be added deliberately with a regression test for durable state updates and rollback safety.
- Last focused commands: `python3 -m unittest control-plane.tests.test_phase28_endpoint_evidence_pack_validation`; `python3 -m unittest control-plane.tests.test_phase23_transition_logging_validation`; `python3 -m compileall control-plane/aegisops_control_plane/service.py control-plane/tests/test_phase28_endpoint_evidence_pack_validation.py`; `node /Users/jp.infra/Dev/codex-supervisor/dist/index.js issue-lint 577 --config /Users/jp.infra/Dev/codex-supervisor/supervisor.config.aegisops.coderabbit.json`; `git commit -m "Fail closed expired endpoint evidence ingest"`; `git push origin codex/issue-577`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
