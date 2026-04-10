# Issue #379: implementation: add reviewed Wazuh single-node lab deployment assets for the first live substrate target

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/379
- Branch: codex/issue-379
- Workspace: .
- Journal: .codex-supervisor/issues/379/issue-journal.md
- Current phase: addressing_review
- Attempt count: 6 (implementation=2, repair=4)
- Last head SHA: 1bba0a29bb72967ee548c609475e5a033afbbb5f
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc56Kfcs
- Repeated failure signature count: 3
- Updated at: 2026-04-10T15:22:01Z

## Latest Codex Summary
Reviewed the one still-unresolved CodeRabbit thread on PR `#384` with the thread-aware `fetch_comments.py` workflow and verified the mount-path portion had already been fixed on `codex/issue-379`. The remaining valid gap was that [render-ossec-integration.sh](ingest/wazuh/single-node-lab/render-ossec-integration.sh) still rendered hardcoded XML while [ossec.integration.sample.xml](ingest/wazuh/single-node-lab/ossec.integration.sample.xml) documented a placeholder contract that depended on `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET`.

I changed the helper to render from the checked-in XML template, load `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET` from `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE`, and substitute both reviewed placeholders into the rendered output. I also updated the asset README, Phase 18 asset doc, verifier, and unit test expectations, reran the focused and full verification stack locally, committed the review fix as `28a0dc4`, committed this journal update as `1bba0a2`, and pushed both commits to `codex/issue-379`. PR `#384` is now on head `1bba0a29bb72967ee548c609475e5a033afbbb5f`; checks had not repopulated yet at the moment of the post-push `gh pr view` refresh.

Summary: Addressed the remaining PR `#384` review-thread contract mismatch by aligning the Wazuh render helper with the reviewed XML template and secret-file bootstrap contract, then reran the focused and full local verification stack.
State hint: addressing_review
Blocked reason: none
Tests: `gh pr view 384 --json number,url,title,reviewDecision,headRefName,headRefOid,statusCheckRollup`; `python3 [REDACTED]/skills/gh-address-comments/scripts/fetch_comments.py TommyKammy/AegisOps 384`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`; `git diff --check`; `git push origin codex/issue-379`; `gh pr view 384 --json number,url,headRefName,headRefOid,statusCheckRollup`
Next action: Wait for PR `#384` to refresh on head `1bba0a2`, then confirm whether CodeRabbit/CI reopen anything before taking further action.
Failure signature: PRRT_kwDOR2iDUc56Kfcs

## Active Failure Context
- Category: review
- Summary: 1 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/384#discussion_r3065033656
- Details:
  - ingest/wazuh/single-node-lab/docker-compose.yml:18 summary=_⚠️ Potential issue_ | _🟠 Major_ **The shared-secret bootstrap contract is internally inconsistent.** Line 13 forwards `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE` into the man... url=https://github.com/TommyKammy/AegisOps/pull/384#discussion_r3065033656

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining unresolved CodeRabbit thread is valid because the reviewed assets still documented `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET` in the XML template while the helper consumed only `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE` and bypassed the template entirely.
- What changed: Updated `ingest/wazuh/single-node-lab/render-ossec-integration.sh` to read `ossec.integration.sample.xml`, load `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET` from `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE`, XML-escape both reviewed values, and substitute them into the rendered output. Updated the surrounding asset docs, verifier, and unit tests to assert the same contract.
- Current blocker: none
- Next exact step: wait for PR `#384` to refresh on `1bba0a2`, then only re-enter review repair if CodeRabbit or CI surfaces a new concrete issue.
- Verification gap: GitHub-side re-review and CI have not yet rerun on pushed head `1bba0a2`, and no live Wazuh manager bring-up was attempted; verification remains at the focused asset/verifier/unit-test layer.
- Files touched: `.codex-supervisor/issues/379/issue-journal.md`, `control-plane/tests/test_phase18_wazuh_single_node_lab_assets.py`, `docs/phase-18-wazuh-single-node-lab-assets.md`, `ingest/wazuh/single-node-lab/README.md`, `ingest/wazuh/single-node-lab/ossec.integration.sample.xml`, `ingest/wazuh/single-node-lab/render-ossec-integration.sh`, `scripts/verify-phase-18-wazuh-lab-topology.sh`
- Rollback concern: Low; reverting this patch would restore the unresolved mismatch between the reviewed template, the `_FILE` bootstrap input, and the render-helper behavior.
- Last focused command: `gh pr view 384 --json number,url,headRefName,headRefOid,statusCheckRollup`
- Last focused commands: `gh pr view 384 --json number,url,title,reviewDecision,headRefName,headRefOid,statusCheckRollup`; `python3 [REDACTED]/skills/gh-address-comments/scripts/fetch_comments.py TommyKammy/AegisOps 384`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`; `git diff --check`; `git commit -m "Align Wazuh lab secret render contract"`; `git commit -m "Update issue 379 journal for review fix"`; `git push origin codex/issue-379`; `gh pr view 384 --json number,url,headRefName,headRefOid,statusCheckRollup`
### Scratchpad
- PR state check: `gh pr view 384 --json ...` showed `verify=SUCCESS` and `CodeRabbit=SUCCESS` on head `3ea5483` before this follow-up review fix.
- Thread inspection result: `fetch_comments.py` showed exactly one unresolved thread, `PRRT_kwDOR2iDUc56Kfcs`, covering the remaining shared-secret/template contract mismatch.
- Focused verification result: `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`, `bash scripts/verify-phase-18-wazuh-lab-topology.sh`, full runtime-unit discovery, and `git diff --check` all pass locally after the template-alignment patch.
- Pending PR action: wait for PR `#384` to repopulate checks and re-review state on head `1bba0a2`.
