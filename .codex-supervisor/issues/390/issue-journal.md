# Issue #390: Phase 18 follow-up: make Wazuh integration render output secret-safe by default

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/390
- Branch: codex/issue-390
- Workspace: .
- Journal: .codex-supervisor/issues/390/issue-journal.md
- Current phase: addressing_review
- Attempt count: 4 (implementation=3, repair=1)
- Last head SHA: 4b2b203e12ca7bc65bdc49aab2d134356bdf511b
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc56R6X0
- Repeated failure signature count: 2
- Updated at: 2026-04-11T05:26:53.366Z

## Latest Codex Summary
The checkpoint is published and reviewable. I pushed `codex/issue-390` to `origin` and opened draft PR [#392](https://github.com/TommyKammy/AegisOps/pull/392) against `main` for commit `4b2b203` (`Harden Wazuh integration render output handling`). The GitHub app could not create the PR because of a `403 Resource not accessible by integration`, so I used `gh pr create` as the fallback.

Focused verification was rerun before opening the PR and passed: `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets control-plane.tests.test_runtime_skeleton`, `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`, and `git check-ignore -v -- ossec.integration.rendered.xml ingest/wazuh/single-node-lab/ossec.integration.rendered.xml foo.ossec.integration.rendered.xml`. I also updated the Codex Working Notes in [issue-journal.md](.codex-supervisor/issues/390/issue-journal.md:1) with the PR link, fresh verification, and next step.

Summary: Pushed `codex/issue-390`, opened draft PR `#392`, reran the requested local verification, and updated the issue journal working notes.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets control-plane.tests.test_runtime_skeleton`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`; `git check-ignore -v -- ossec.integration.rendered.xml ingest/wazuh/single-node-lab/ossec.integration.rendered.xml foo.ossec.integration.rendered.xml`
Next action: Monitor draft PR `#392` for CI/manual review feedback and address any follow-up if checks or comments arrive.
Failure signature: PRRT_kwDOR2iDUc56R6X0

## Active Failure Context
- Category: review
- Summary: 1 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/392#discussion_r3067639173
- Details:
  - control-plane/tests/test_phase18_wazuh_single_node_lab_assets.py:215 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Avoid pre-existing-file flakiness in the repo-root negative test.** At Line 214, the test can fail if `REPO_ROOT/ossec.integration.rendered.x... url=https://github.com/TommyKammy/AegisOps/pull/392#discussion_r3067639173

## Codex Working Notes
### Current Handoff
- Hypothesis: The unsafe default came from `render-ossec-integration.sh` using an implicit current-directory output path (`./ossec.integration.rendered.xml`), which allows secret-bearing output to land in tracked worktree locations during repo-root usage.
- What changed: Kept the reviewed Phase 18 hardening intact and addressed the remaining PR thread by making the repo-root negative unittest preserve pre-existing `REPO_ROOT/ossec.integration.rendered.xml` state. The test now records existence plus `st_mtime_ns` before invoking the helper and asserts the helper did not create or modify that path on failure.
- Current blocker: none
- Next exact step: Commit the review-thread fix, push `codex/issue-390`, and update PR `#392`.
- Verification gap: none for the requested local scope after rerunning the focused Phase 18 verification set on the review-fix diff.
- Files touched: `.gitignore`, `control-plane/tests/test_phase18_wazuh_single_node_lab_assets.py`, `docs/phase-18-wazuh-single-node-lab-assets.md`, `ingest/wazuh/single-node-lab/README.md`, `ingest/wazuh/single-node-lab/render-ossec-integration.sh`, `scripts/verify-phase-18-wazuh-lab-topology.sh`
- Rollback concern: Low; the behavioral change is intentionally narrow but operators now must pass an explicit output path when rendering the Wazuh integration block.
- Last focused command:
- Last focused commands: `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets control-plane.tests.test_runtime_skeleton`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`; `git check-ignore -v -- ossec.integration.rendered.xml ingest/wazuh/single-node-lab/ossec.integration.rendered.xml foo.ossec.integration.rendered.xml`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
