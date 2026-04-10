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
Committed and pushed `0990d28` (`Fix Phase 18 Wazuh lab review contract`) to `codex/issue-379`.

The review fix aligns the Wazuh lab assets around an explicit render workflow instead of implying runtime env expansion: [render-ossec-integration.sh](ingest/wazuh/single-node-lab/render-ossec-integration.sh), [ossec.integration.sample.xml](ingest/wazuh/single-node-lab/ossec.integration.sample.xml), [docker-compose.yml](ingest/wazuh/single-node-lab/docker-compose.yml), and [bootstrap.env.sample](ingest/wazuh/single-node-lab/bootstrap.env.sample) now use one coherent secret-path/render contract. I also tightened [test_phase18_wazuh_single_node_lab_assets.py](control-plane/tests/test_phase18_wazuh_single_node_lab_assets.py) and [verify-phase-18-wazuh-lab-topology.sh](scripts/verify-phase-18-wazuh-lab-topology.sh) so `github_audit` scope drift and template/render regressions fail locally, and updated the issue journal without reintroducing any machine-local path.

Focused verification passed locally. After the push, `gh pr checks 384` shows `verify` pending and `CodeRabbit` pending/review in progress on the new head. The render-step change follows Wazuh’s official integration docs, which document literal `<hook_url>` / `<api_key>` config values and passing them to custom scripts as arguments: https://documentation.wazuh.com/current/user-manual/reference/ossec-conf/integration.html and https://documentation.wazuh.com/current/user-manual/manager/integration-with-external-apis.html

Summary: Pushed `0990d28` with the remaining PR #384 review fixes: redacted journal command history, added a reviewed Wazuh integration render helper, aligned the secret-file contract, and tightened Phase 18 verifier/test coverage.
State hint: waiting_ci
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_lab_topology_docs`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/verify-compose-skeleton-validation.sh`; `git diff --check`; `gh pr checks 384`
Next action: Monitor PR `#384` on head `0990d28` for the new `verify` and CodeRabbit results, and address only if a fresh concrete failure or review finding appears.
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
- Next exact step: commit and push the Bash-portability fix to `codex/issue-379`, then confirm PR `#384` reruns `verify` on the refreshed head and clears the failing runtime-unit-test step.
- Verification gap: No GitHub-side rerun has completed against the portability fix yet, and no live Wazuh manager bring-up was attempted; verification remained at the focused helper/test/verifier and full runtime-unit-test layer.
- Files touched: `.codex-supervisor/issues/379/issue-journal.md`, `ingest/wazuh/single-node-lab/render-ossec-integration.sh`
- Rollback concern: Low; reverting this patch would reintroduce the Bash 5 XML-escape regression that currently fails PR `#384` in GitHub Actions.
- Last focused command: `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`
- Last focused commands: `gh pr view 384 --json number,url,title,headRefName,baseRefName,headRefOid,statusCheckRollup`; `python3 [REDACTED]/skills/gh-fix-ci/scripts/inspect_pr_checks.py --repo . --pr 384 --json`; `gh run view 24249517759 --json name,workflowName,conclusion,status,url,event,headBranch,headSha,jobs`; `gh run view 24249517759 --log`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets.Phase18WazuhSingleNodeLabAssetsTests.test_render_helper_materializes_literal_integration_values`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'`; `git diff --check`
### Scratchpad
- CI reproduction result: `gh run view 24249517759 --log` shows `python3 -m unittest discover -s control-plane/tests -p 'test_*.py'` failing only `test_render_helper_materializes_literal_integration_values` because Actions rendered `<api_key>reviewed<lt;&amp;>gt;secret</api_key>` instead of `<api_key>reviewed&lt;&amp;&gt;secret</api_key>`.
- Focused verification result: the exact failing Phase 18 render-helper test, `bash scripts/verify-phase-18-wazuh-lab-topology.sh`, full runtime-unit discovery, and `git diff --check` all pass locally after the `sed`-based escaping fix.
- Pending PR action: push the portability-fix commit and re-check PR `#384` on the refreshed head.
