# Phase 18 Wazuh Lab Topology and Live Ingest Contract Validation

- Validation date: 2026-04-10
- Validation scope: Phase 18 review of the approved single-node Wazuh lab target, the bootable AegisOps control-plane runtime boundary it connects to, the reviewed repository-local Wazuh lab deployment assets, GitHub audit as the approved first live source family, Wazuh -> AegisOps as the mainline live path, fail-closed expectations for transport, authentication, and payload admission, and confirmation that OpenSearch runtime enrichment, thin operator UI, and guarded automation live wiring remain deferred
- Baseline references: `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md`, `docs/phase-18-wazuh-single-node-lab-assets.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/wazuh-alert-ingest-contract.md`, `docs/source-onboarding-contract.md`, `docs/source-families/github-audit/onboarding-package.md`, `docs/architecture.md`
- Verification commands: `python3 -m unittest control-plane.tests.test_phase18_wazuh_lab_topology_docs`, `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`, `bash scripts/verify-phase-18-wazuh-lab-topology.sh`, `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`
- Validation status: PASS

## Required Boundary Artifacts

- `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md`
- `docs/phase-18-wazuh-lab-topology-validation.md`
- `docs/phase-18-wazuh-single-node-lab-assets.md`
- `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`
- `docs/phase-16-release-state-and-first-boot-scope.md`
- `docs/wazuh-alert-ingest-contract.md`
- `docs/source-onboarding-contract.md`
- `docs/source-families/github-audit/onboarding-package.md`
- `docs/architecture.md`
- `ingest/wazuh/single-node-lab/README.md`
- `ingest/wazuh/single-node-lab/bootstrap.env.sample`
- `ingest/wazuh/single-node-lab/docker-compose.yml`
- `ingest/wazuh/single-node-lab/ossec.integration.sample.xml`
- `scripts/verify-phase-18-wazuh-lab-topology.sh`
- `scripts/test-verify-phase-18-wazuh-lab-topology.sh`

## Review Outcome

Confirmed the approved topology is limited to one single-node Wazuh lab target feeding one bootable AegisOps control-plane runtime boundary through the reviewed reverse proxy and into PostgreSQL-backed control-plane state.

Confirmed the Phase 18 live path keeps Wazuh -> AegisOps as the mainline live path and does not broaden the first live slice into `Wazuh -> Shuffle`, n8n relay routing, or OpenSearch-first runtime dependence.

Confirmed GitHub audit is the approved first live source family because it preserves the narrowest identity-rich source context already prioritized by the reviewed Phase 14 family order and GitHub audit onboarding package.

Confirmed the reviewed Wazuh custom integration contract requires HTTPS POST to the approved reverse-proxy ingress boundary plus `Authorization: Bearer <shared secret>` authentication sourced from an untracked runtime secret.

Confirmed the Phase 18 contract applies the existing Wazuh payload-admission rules rather than redefining them, and limits first live admission to GitHub audit carried inside the reviewed Wazuh alert envelope.

Confirmed the reviewed repository-local asset bundle under `ingest/wazuh/single-node-lab/` makes the first live substrate target explicit with placeholder-safe compose, bootstrap, and integration artifacts while keeping secrets untracked and production hardening out of scope.

Confirmed the live ingest path remains fail-closed by rejecting non-HTTPS requests, non-POST requests, missing or invalid bearer credentials, direct backend bypass attempts, invalid JSON payloads, Wazuh payloads that violate required field expectations, and payloads outside the approved first live family.

Confirmed OpenSearch runtime enrichment, thin operator UI, guarded automation live wiring, broader source-family rollout, direct GitHub API actioning, and production-scale Wazuh topologies remain deferred and out of scope for this slice.

The issue requested review against `Phase 16-21 Epic Roadmap.md`, but that roadmap file was not present in the local worktree and could not be located via repository search during this turn.

## Cross-Link Review

`docs/phase-17-runtime-config-contract-and-boot-command-expectations.md` must continue to define the bootable runtime contract that the first live topology connects to without adding new startup blockers.

`docs/phase-16-release-state-and-first-boot-scope.md` must continue to define the narrow first-boot floor so Phase 18 live wiring does not silently broaden the required runtime.

`docs/wazuh-alert-ingest-contract.md` must continue to define the reviewed Wazuh-native required fields, provenance expectations, and identifier mapping that the live path preserves.

`docs/source-onboarding-contract.md` and `docs/source-families/github-audit/onboarding-package.md` must continue to keep GitHub audit scoped as a reviewed source-family baseline rather than a blanket approval for broad live source rollout.

`docs/phase-18-wazuh-single-node-lab-assets.md` and `ingest/wazuh/single-node-lab/` must continue to keep the reviewed lab deployment assets explicit without turning them into implicit approval for production-scale Wazuh.

`docs/architecture.md` must continue to keep AegisOps as the authority boundary and forbid detection-substrate or automation-substrate shortcuts from becoming the policy-sensitive system-of-record path.

## Deviations

- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.
