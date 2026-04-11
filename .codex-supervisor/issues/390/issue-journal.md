# Issue #390: Phase 18 follow-up: make Wazuh integration render output secret-safe by default

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/390
- Branch: codex/issue-390
- Workspace: .
- Journal: .codex-supervisor/issues/390/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 3da085b867906428f7179ad14746d5577ad68968
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-11T05:04:39.495Z

## Latest Codex Summary
- Reproduced that `ingest/wazuh/single-node-lab/render-ossec-integration.sh` defaulted to `./ossec.integration.rendered.xml` and would write a secret-bearing rendered integration file from repo root with no explicit output argument.
- Hardened the helper to require an explicit output path, print a reviewed safe temp-location example, and added `.gitignore` coverage for rendered `ossec.integration.rendered.xml` artifacts.
- Updated the Phase 18 lab asset test, asset documentation, asset README, and Phase 18 verifier to enforce the secret-safe render workflow.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The unsafe default came from `render-ossec-integration.sh` using an implicit current-directory output path (`./ossec.integration.rendered.xml`), which allows secret-bearing output to land in tracked worktree locations during repo-root usage.
- What changed: Added a focused failing unittest for the no-argument render path, changed the helper to reject implicit output paths and print `\${TMPDIR:-/tmp}/aegisops-wazuh/ossec.integration.rendered.xml` as the reviewed safe example, added rendered-artifact ignore patterns to `.gitignore`, and updated Phase 18 asset docs/README/verifier expectations to match.
- Current blocker: none
- Next exact step: Commit the verified secret-safe render-flow hardening on `codex/issue-390`.
- Verification gap: none for the requested local scope; PR/CI is still absent because no PR exists yet.
- Files touched: `.gitignore`, `control-plane/tests/test_phase18_wazuh_single_node_lab_assets.py`, `docs/phase-18-wazuh-single-node-lab-assets.md`, `ingest/wazuh/single-node-lab/README.md`, `ingest/wazuh/single-node-lab/render-ossec-integration.sh`, `scripts/verify-phase-18-wazuh-lab-topology.sh`
- Rollback concern: Low; the behavioral change is intentionally narrow but operators now must pass an explicit output path when rendering the Wazuh integration block.
- Last focused command: `git check-ignore -v ingest/wazuh/single-node-lab/ossec.integration.rendered.xml`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
