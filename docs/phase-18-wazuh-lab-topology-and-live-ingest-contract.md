# AegisOps Phase 18 Wazuh Lab Topology and Live Ingest Contract

## 1. Purpose

This document defines the approved Phase 18 lab topology, first live source family, and reviewed live ingest contract for the first narrow Wazuh-backed runtime slice.

It supplements `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, `docs/phase-16-release-state-and-first-boot-scope.md`, `docs/wazuh-alert-ingest-contract.md`, `docs/source-onboarding-contract.md`, `docs/architecture.md`, and `docs/source-families/github-audit/onboarding-package.md`.

This document defines reviewed topology and ingest-contract scope only. It does not approve broader source-family rollout, OpenSearch runtime enrichment, a thin operator UI, guarded automation live wiring, or production-scale Wazuh deployment topologies.

The reviewed repository-local asset bundle for this topology lives under `ingest/wazuh/single-node-lab/` and remains placeholder-safe lab scaffolding rather than production deployment truth.

## 2. Approved Phase 18 Lab Topology

The approved Phase 18 lab topology is one single-node Wazuh lab target connected to one bootable AegisOps control-plane runtime boundary.

The approved topology components are:

- one single-node Wazuh manager as the upstream detection substrate and reviewed webhook sender;
- one reviewed reverse proxy as the only approved external ingress path into AegisOps;
- one bootable AegisOps control-plane runtime boundary rooted under `control-plane/`; and
- one PostgreSQL datastore for AegisOps-owned control-plane state.

The approved Phase 18 live path is:

`single-node Wazuh -> reviewed reverse proxy -> bootable AegisOps control-plane runtime boundary -> PostgreSQL`

Phase 18 therefore turns the Phase 17 boot path into one reviewed live substrate path without broadening the first-boot runtime floor.

The control-plane backend port remains internal-only behind the reverse proxy.

The approved topology must not publish the control-plane backend port directly to user networks or the public internet.

The approved topology must not require OpenSearch, Shuffle, n8n, the thin operator UI, or the guarded executor path to count as the first live slice.

## 3. Approved First Live Source Family

The Approved First Live Source Family for the initial Phase 18 slice is GitHub audit.

GitHub audit remains the first priority family from the reviewed Phase 14 ordering and is the narrowest identity-rich family that already preserves actor, target, repository or organization context, privilege-change metadata, and provenance detail through the reviewed Wazuh path.

Phase 18 approves GitHub audit as the first live source family because it keeps the first live ingest path reviewable without reopening the broader source-family problem.

The Phase 18 live-family decision does not make GitHub a direct actioning substrate and does not authorize non-audit GitHub telemetry families.

The following remain explicitly deferred source families for this slice:

- Entra ID;
- Microsoft 365 audit; and
- any broader endpoint, network, SaaS, or generic cross-platform telemetry family.

## 4. Reviewed Wazuh Custom Integration Live Ingest Contract

### 4.1 Transport and Path

The reviewed Wazuh custom integration must send one Wazuh alert JSON object at a time to AegisOps using HTTPS POST.

The approved external ingress target is the reviewed reverse proxy path for the AegisOps intake boundary, not a directly exposed control-plane backend port.

The approved live path is Wazuh -> AegisOps.

Phase 18 must not make `Wazuh -> Shuffle` part of the first live slice.

The custom integration must not route the first live slice through Shuffle, n8n, OpenSearch, or any sidecar relay before the AegisOps control-plane boundary admits the payload.

### 4.2 Authentication

The reviewed request authentication contract is `Authorization: Bearer <shared secret>`.

The shared secret is an AegisOps-owned runtime secret and must come from an untracked secret source or reviewed operator-provided runtime secret file.

Wazuh and the AegisOps reverse proxy must share the same reviewed bearer secret for this live path.

Alternate authentication schemes, query-string secrets, anonymous webhook access, or substrate-local trust-by-network-location are out of contract for the first live slice.

### 4.3 Payload Admission Boundary

The payload shape remains the reviewed Wazuh alert contract from `docs/wazuh-alert-ingest-contract.md`.

Phase 18 does not redefine the Wazuh-native field contract. It applies that contract to one reviewed live path.

For the first live slice, the admitted payload family is GitHub audit carried inside the reviewed Wazuh alert envelope.

The control-plane boundary must preserve the full raw Wazuh payload, Wazuh-native identifier, upstream timestamp, rule provenance, and accountable source identity exactly as required by the Wazuh ingest contract.

### 4.4 Fail-Closed Expectations

The live ingest path must fail closed.

Ingress must reject the request when any of the following conditions hold:

- the request is not HTTPS at the approved ingress boundary;
- the request does not use HTTPS POST;
- the `Authorization: Bearer` header is missing, empty, malformed, or does not match the reviewed shared secret;
- the request attempts to bypass the approved reverse proxy and reach the control-plane backend directly;
- the payload is not valid JSON;
- the payload does not satisfy the reviewed Wazuh required fields including `id`, `timestamp`, `rule.id`, `rule.level`, `rule.description`, accountable source identity, and raw payload preservation expectations; or
- the payload represents a family other than the approved GitHub audit first live source family.

Fail closed in this phase means the request is rejected, downstream alert or case truth is not minted from the invalid payload, and no fallback automation route is used as a substitute for the rejected control-plane admission.

The live ingest path must not silently downgrade to HTTP, accept missing authentication, bypass the reviewed Wazuh contract, or treat `Wazuh -> Shuffle` as a fallback route.

## 5. Deferred Runtime Surfaces and Non-Goals

The following remain visibly deferred and out of scope for the Phase 18 first live slice:

- broader source-family rollout beyond GitHub audit;
- OpenSearch runtime enrichment or OpenSearch-dependent success criteria;
- thin operator UI work;
- guarded automation live wiring;
- direct GitHub API actioning or response execution;
- multi-node, HA, or production-scale Wazuh topologies; and
- any topology that makes Wazuh, Shuffle, or another substrate the authority for alert, case, approval, evidence, or reconciliation truth.

## 6. Alignment and Non-Expansion Rules

Phase 18 is aligned to the reviewed Phase 16 and Phase 17 baseline by keeping the bootable AegisOps control-plane runtime boundary narrow and by adding only one reviewed live intake path.

`docs/phase-16-release-state-and-first-boot-scope.md` remains the normative source for the approved first-boot runtime floor.

`docs/phase-17-runtime-config-contract-and-boot-command-expectations.md` remains the normative source for the bootable runtime contract that this live topology connects to.

`docs/wazuh-alert-ingest-contract.md` remains the normative source for the Wazuh payload contract.

`docs/source-onboarding-contract.md` and `docs/source-families/github-audit/onboarding-package.md` remain the normative source-family review references for why GitHub audit is the first live family.

`docs/phase-18-wazuh-single-node-lab-assets.md` and `ingest/wazuh/single-node-lab/` remain the normative reviewed asset references for the first live lab substrate target.

Any implementation that adds alternate live routing, broader source admission, direct backend publication, or optional-surface startup blockers is out of contract for Phase 18.
