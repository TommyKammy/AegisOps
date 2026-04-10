# Issue #379: implementation: add reviewed Wazuh single-node lab deployment assets for the first live substrate target

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/379
- Branch: codex/issue-379
- Workspace: .
- Journal: .codex-supervisor/issues/379/issue-journal.md
- Current phase: addressing_review
- Attempt count: 4 (implementation=2, repair=2)
- Last head SHA: 96d803658f8eb144cd392b8c6455deab3f6dfee5
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc56Kfco|PRRT_kwDOR2iDUc56Kfcs|PRRT_kwDOR2iDUc56Kfcu|PRRT_kwDOR2iDUc56Kfcz
- Repeated failure signature count: 1
- Updated at: 2026-04-10T14:55:51.191Z

## Latest Codex Summary
Addressed the remaining automated review threads on PR #384 by keeping the issue journal path-redacted, aligning the Wazuh shared-secret contract around the mounted `/run/aegisops-secrets/...` path, documenting that the sample integration must be rendered before use because Wazuh reads those fields literally, adding a reviewed `render-ossec-integration.sh` helper, and tightening the Phase 18 verifier/tests to assert the `github_audit` scope and render workflow.

Focused local verification now passes for the updated asset bundle, verifier, and compose skeleton boundary. The branch still needs the review-fix commit pushed so PR #384 can rerun checks and refresh the automated review state on the new head.

Summary: Addressed the outstanding PR #384 automated review findings by redacting the journal command path, adding a reviewed Wazuh integration render helper, aligning the secret-file/render contract across the lab assets, and extending tests/verifier coverage for the `github_audit` guardrail.
State hint: addressing_review
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_lab_topology_docs`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/verify-compose-skeleton-validation.sh`; `git diff --check`
Next action: Push the review-fix commit to PR `#384`, then confirm the refreshed head clears the automated review threads and reruns the relevant checks cleanly.
Failure signature: none

## Active Failure Context
- Category: review
- Summary: 4 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/384#discussion_r3065033652
- Details:
  - .codex-supervisor/issues/379/issue-journal.md:46 summary=_⚠️ Potential issue_ | _🟠 Major_ **Drop the machine-specific absolute path from the committed journal.** Line 46 embeds a local `<redacted-local-path>.` path and username in a tra... url=https://github.com/TommyKammy/AegisOps/pull/384#discussion_r3065033652
  - ingest/wazuh/single-node-lab/docker-compose.yml:18 summary=_⚠️ Potential issue_ | _🟠 Major_ **The shared-secret bootstrap contract is internally inconsistent.** Line 13 forwards `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE` into the man... url=https://github.com/TommyKammy/AegisOps/pull/384#discussion_r3065033656
  - ingest/wazuh/single-node-lab/ossec.integration.sample.xml:5 summary=_⚠️ Potential issue_ | _🟠 Major_ 🧩 Analysis chain 🌐 Web query: `Does Wazuh support environment variable expansion like ${VAR} inside the configuration used for custom webhook... url=https://github.com/TommyKammy/AegisOps/pull/384#discussion_r3065033659
  - scripts/verify-phase-18-wazuh-lab-topology.sh:223 summary=_⚠️ Potential issue_ | _🟡 Minor_ **Pin the integration’s GitHub-audit scope in the verifier.** These checks never assert ` github_audit `, which is the field that actually keep... url=https://github.com/TommyKammy/AegisOps/pull/384#discussion_r3065033666

## Codex Working Notes
### Current Handoff
- Hypothesis: The remaining review blockers are local asset-contract issues rather than a broader topology problem: the sample Wazuh integration needs an explicit render step, the shared-secret path needs one consistent mounted-path contract, and the verifier/test suite needs to pin the GitHub-audit scope so the first-live boundary cannot drift silently.
- What changed: Updated `ingest/wazuh/single-node-lab/bootstrap.env.sample` to use the mounted `/run/aegisops-secrets/...` secret-file path, added `ingest/wazuh/single-node-lab/render-ossec-integration.sh` to render literal `<hook_url>` and `<api_key>` values, documented the render requirement in the sample XML, README, asset doc, and validation record, mounted the render helper into the placeholder manager config path in `docker-compose.yml`, tightened `scripts/verify-phase-18-wazuh-lab-topology.sh` and `scripts/test-verify-phase-18-wazuh-lab-topology.sh`, and extended `control-plane/tests/test_phase18_wazuh_single_node_lab_assets.py` with render-helper coverage plus the `github_audit` assertion.
- Current blocker: none
- Next exact step: commit and push the review-fix patch to `codex/issue-379`, then confirm PR `#384` reruns `verify`/CodeRabbit on the new head and no new review findings appear.
- Verification gap: No live Wazuh manager bring-up or GitHub-side rerun against the new local patch was performed here; verification stayed at the focused doc/asset/unit/verifier layer plus compose skeleton validation.
- Files touched: `.codex-supervisor/issues/379/issue-journal.md`, `control-plane/tests/test_phase18_wazuh_single_node_lab_assets.py`, `docs/phase-18-wazuh-lab-topology-validation.md`, `docs/phase-18-wazuh-single-node-lab-assets.md`, `ingest/wazuh/single-node-lab/README.md`, `ingest/wazuh/single-node-lab/bootstrap.env.sample`, `ingest/wazuh/single-node-lab/docker-compose.yml`, `ingest/wazuh/single-node-lab/ossec.integration.sample.xml`, `ingest/wazuh/single-node-lab/render-ossec-integration.sh`, `scripts/verify-phase-18-wazuh-lab-topology.sh`, `scripts/test-verify-phase-18-wazuh-lab-topology.sh`
- Rollback concern: Low to moderate; reverting this patch would reopen the review-thread concerns around unsupported Wazuh placeholder expansion, ambiguous secret-path handling, and missing verifier coverage for the GitHub-audit scope.
- Last focused command: `git diff --check`
- Last focused commands: `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_lab_topology_docs`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/verify-compose-skeleton-validation.sh`; `git diff --check`
### Scratchpad
- Review-fix result: the lab asset bundle now carries an explicit render helper and mounted secret-path contract instead of implying that Wazuh expands `${...}` placeholders at runtime.
- Focused verification result: the updated Phase 18 unit tests, topology verifier, verifier harness, compose skeleton validation, and `git diff --check` all pass locally.
- Pending PR action: push the review-fix commit and re-check PR `#384` on the refreshed head.
