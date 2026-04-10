# Issue #379: implementation: add reviewed Wazuh single-node lab deployment assets for the first live substrate target

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/379
- Branch: codex/issue-379
- Workspace: .
- Journal: .codex-supervisor/issues/379/issue-journal.md
- Current phase: repairing_ci
- Attempt count: 3 (implementation=2, repair=1)
- Last head SHA: 4c94b4bc77b13cc6e26e09b4f98ebf825e41723f
- Blocked reason: none
- Last failure signature: verify:fail
- Repeated failure signature count: 3
- Updated at: 2026-04-10T14:16:37.095Z

## Latest Codex Summary
Published the existing checkpoint for issue #379. `codex/issue-379` is pushed, the focused verification set passed again, and the draft PR is open at `https://github.com/TommyKammy/AegisOps/pull/384`.

The GitHub app could not create the PR because it hit `403 Resource not accessible by integration`, so I used the approved `gh pr create --draft` fallback. No implementation changes were needed in this turn; I only updated the supervisor journal. The only local uncommitted changes now are the journal update and supervisor scratch files.

Summary: Revalidated the committed Phase 18 Wazuh lab asset bundle, pushed `codex/issue-379`, and opened draft PR #384 against `main`.
State hint: draft_pr
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_lab_topology_docs`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`
Next action: Monitor draft PR #384 for reviewer feedback or CI and address any follow-up issues from the published checkpoint.
Failure signature: verify:fail

## Active Failure Context
- Category: checks
- Summary: PR #384 has failing checks.
- Command or source: gh pr checks
- Reference: https://github.com/TommyKammy/AegisOps/pull/384
- Details:
  - verify (fail/FAILURE) https://github.com/TommyKammy/AegisOps/actions/runs/24247205331/job/70796598792

## Codex Working Notes
### Current Handoff
- Hypothesis: The failing `verify` check is caused by `ingest/wazuh/single-node-lab/docker-compose.yml` publishing host ports under `ingest/`, which violates the repo-wide compose skeleton validation that forbids direct backend `ports:` publication in checked compose assets.
- What changed: Reproduced `bash scripts/verify-compose-skeleton-validation.sh` locally, changed the Wazuh lab compose asset from host-published `ports:` to internal-only `expose:` declarations, documented the internal-only lab access boundary in the Phase 18 asset doc and README, and extended the Phase 18 unit/verifier coverage to reject future direct host port publication.
- Current blocker: none
- Next exact step: commit the CI repair, push `codex/issue-379`, and watch PR `#384` for the rerun of `verify`.
- Verification gap: No live Wazuh runtime bring-up or full GitHub Actions workflow rerun was performed locally; verification remained at the repo verifier plus focused Phase 18 doc-and-asset contract layer.
- Files touched: `control-plane/tests/test_phase18_wazuh_single_node_lab_assets.py`, `docs/phase-18-wazuh-single-node-lab-assets.md`, `ingest/wazuh/single-node-lab/README.md`, `ingest/wazuh/single-node-lab/docker-compose.yml`, `scripts/verify-phase-18-wazuh-lab-topology.sh`, `scripts/test-verify-phase-18-wazuh-lab-topology.sh`
- Rollback concern: Low; the repair narrows the new Wazuh lab asset to the already-approved internal-only exposure model, but reverting it will reintroduce the repo-wide compose verifier failure.
- Last focused command: `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`
- Last focused commands: `python3 /Users/jp.infra/.codex/plugins/cache/openai-curated/github/fb0a18376bcd9f2604047fbe7459ec5aed70c64b/skills/gh-fix-ci/scripts/inspect_pr_checks.py --repo . --pr 384`; `bash scripts/verify-compose-skeleton-validation.sh`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`; `python3 -m unittest control-plane.tests.test_phase18_wazuh_lab_topology_docs`; `bash scripts/verify-phase-18-wazuh-lab-topology.sh`; `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`
### Scratchpad
- CI failure reproduced from GitHub Actions log and locally as `Checked compose skeletons must not publish backend services directly with ports.`
- Local repair result: compose skeleton validation and focused Phase 18 verification set all pass after removing direct host port publication from the Wazuh lab asset.
