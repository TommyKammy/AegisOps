# Issue #379: implementation: add reviewed Wazuh single-node lab deployment assets for the first live substrate target

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/379
- Branch: codex/issue-379
- Workspace: .
- Journal: .codex-supervisor/issues/379/issue-journal.md
- Current phase: repairing_ci
- Attempt count: 5 (implementation=2, repair=3)
- Last head SHA: 0990d2885ca200047512cd50672da024da905641
- Blocked reason: none
- Last failure signature: verify:fail
- Repeated failure signature count: 3
- Updated at: 2026-04-10T15:08:02.496Z

## Latest Codex Summary
Committed and pushed `4f7444d` (`Fix Wazuh render helper XML escaping`) to `codex/issue-379`.

After reproducing the failing `verify` job with `gh run view 24249517759 --log`, I confirmed the new regression was not a topology mismatch but a Bash-version portability bug in [render-ossec-integration.sh](ingest/wazuh/single-node-lab/render-ossec-integration.sh): GitHub Actions Bash 5 rendered `<api_key>reviewed<lt;&amp;>gt;secret</api_key>` while local Bash 3.2 did not. Replacing the helper's parameter-expansion XML escaping with a `sed`-based escaper makes the rendered `<hook_url>` and `<api_key>` deterministic across shells while preserving the reviewed `github_audit` contract.

Focused verification passed locally with the exact failing test, the Phase 18 topology verifier, the full `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'` command used by CI, and `git diff --check`. After the push, PR `#384` advanced to head `4f7444d01de5c895f16ffec68f8bd0f98e69df1e` and `gh pr checks 384` shows a fresh `verify` run queued at https://github.com/TommyKammy/AegisOps/actions/runs/24249833612/job/70805863727.

Summary: Pushed `4f7444d` to fix the PR #384 `verify` failure by making the Wazuh render helper's XML escaping Bash-version-stable, and confirmed GitHub queued a fresh `verify` run on the new head.
State hint: repairing_ci
Blocked reason: none
Tests: `gh pr view 384 --json number,url,title,headRefName,baseRefName,headRefOid,statusCheckRollup`; `python3 [REDACTED]/skills/gh-fix-ci/scripts/inspect_pr_checks.py --repo . --pr 384 --json`; `gh run view 24249517759 --json name,workflowName,conclusion,status,url,event,headBranch,headSha,jobs`; `gh run view 24249517759 --log`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets.Phase18WazuhSingleNodeLabAssetsTests.test_render_helper_materializes_literal_integration_values`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`; `git diff --check`; `git push origin codex/issue-379`; `gh pr checks 384`
Next action: Monitor the queued `verify` run for PR `#384` on head `4f7444d`, and only re-enter repair work if that rerun reports a new concrete failure.
Failure signature: verify:fail

## Active Failure Context
- Category: checks
- Summary: PR #384 has failing checks.
- Command or source: gh pr checks
- Reference: https://github.com/TommyKammy/AegisOps/pull/384
- Details:
  - verify (fail/FAILURE) https://github.com/TommyKammy/AegisOps/actions/runs/24249517759/job/70804732783

## Codex Working Notes
### Current Handoff
- Hypothesis: The current `verify` failure is a Bash-version portability bug inside `ingest/wazuh/single-node-lab/render-ossec-integration.sh`: the helper's parameter-expansion XML escaping passes under local Bash 3.2 but mis-escapes `<` and `>` under GitHub Actions Bash 5, breaking the Phase 18 render-helper unit test.
- What changed: Replaced the helper's Bash parameter-expansion XML escaping with a `sed`-based escaper in `ingest/wazuh/single-node-lab/render-ossec-integration.sh` so the rendered `<api_key>` value stays XML-safe across Bash versions and continues to preserve the reviewed `github_audit` scope.
- Current blocker: none
- Next exact step: wait for the queued GitHub `verify` rerun on head `4f7444d`, and only resume debugging if that rerun exposes a different concrete failure.
- Verification gap: No GitHub-side rerun has completed yet against `4f7444d`, and no live Wazuh manager bring-up was attempted; verification remained at the focused helper/test/verifier and full runtime-unit-test layer.
- Files touched: `.codex-supervisor/issues/379/issue-journal.md`, `ingest/wazuh/single-node-lab/render-ossec-integration.sh`
- Rollback concern: Low; reverting this patch would reintroduce the Bash 5 XML-escape regression that currently fails PR `#384` in GitHub Actions.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
- Last focused commands: `gh pr view 384 --json number,url,title,headRefName,baseRefName,headRefOid,statusCheckRollup`; `python3 [REDACTED]/skills/gh-fix-ci/scripts/inspect_pr_checks.py --repo . --pr 384 --json`; `gh run view 24249517759 --json name,workflowName,conclusion,status,url,event,headBranch,headSha,jobs`; `gh run view 24249517759 --log`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets.Phase18WazuhSingleNodeLabAssetsTests.test_render_helper_materializes_literal_integration_values`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`; `git diff --check`
### Scratchpad
- CI reproduction result: `gh run view 24249517759 --log` shows `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'` failing only `test_render_helper_materializes_literal_integration_values` because Actions rendered `<api_key>reviewed<lt;&amp;>gt;secret</api_key>` instead of `<api_key>reviewed&lt;&amp;&gt;secret</api_key>`.
- Focused verification result: the exact failing Phase 18 render-helper test, `bash scripts/verify-phase-18-wazuh-lab-topology.sh`, full runtime-unit discovery, and `git diff --check` all pass locally after the `sed`-based escaping fix.
- Pending PR action: wait for the queued PR `#384` `verify` rerun on head `4f7444d`.
