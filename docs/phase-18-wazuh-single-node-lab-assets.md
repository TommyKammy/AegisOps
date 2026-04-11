# Phase 18 Wazuh Single-Node Lab Assets

## 1. Purpose

This document defines the reviewed repository-local deployment assets for the Phase 18 single-node Wazuh lab target.

It supplements `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, `docs/wazuh-alert-ingest-contract.md`, `docs/source-families/github-audit/onboarding-package.md`, and `docs/compose-skeleton-overview.md`.

This document defines reviewed lab assets, bootstrap inputs, and operator expectations only. It is not an approved production deployment, does not approve multi-node or production-scale Wazuh, and does not make the optional OpenSearch runtime extension, thin operator UI, or guarded automation live wiring part of the first live slice.

## 2. Asset Bundle

The reviewed asset bundle for the single-node Wazuh lab target lives under `ingest/wazuh/single-node-lab/`.

The reviewed bundle contains:

- `docker-compose.yml` for the placeholder-safe single-node Wazuh manager, indexer, and dashboard lab stack with internal-only service exposure and no direct host port publication;
- `bootstrap.env.sample` for reviewed non-secret bootstrap inputs;
- `ossec.integration.sample.xml` for the reviewed custom integration shape that preserves `Wazuh -> AegisOps` as the only approved first live routing path;
- `render-ossec-integration.sh` for rendering the reviewed sample into literal Wazuh integration values before operator use; and
- `README.md` for operator expectations, deferred-scope reminders, and path-local usage notes.

These artifacts exist so the repository contains one explicit substrate target for the first live ingest path without implying a broader Wazuh rollout.

## 3. Reviewed Bootstrap Inputs

The reviewed bootstrap inputs for this asset package are:

- `AEGISOPS_WAZUH_HOSTNAME` for the single-node Wazuh manager name;
- `AEGISOPS_WAZUH_INDEXER_HOSTNAME` for the co-located indexer name;
- `AEGISOPS_WAZUH_DASHBOARD_HOSTNAME` for the co-located dashboard name;
- `AEGISOPS_WAZUH_AEGISOPS_INGEST_URL` for the reviewed reverse-proxy HTTPS endpoint that receives the live payload;
- `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE` for the mounted runtime secret file that provides the shared bearer secret to the reviewed render helper; and
- `AEGISOPS_WAZUH_GITHUB_AUDIT_ENROLLMENT_STATUS=reviewed-first-live-family-only` to keep the approved GitHub audit scope explicit for operators.

The reviewed custom integration shape uses `Authorization: Bearer <shared secret>` at runtime.

The shared secret must remain untracked and must come from an operator-provided runtime secret file or another reviewed untracked secret source.

The reviewed reverse proxy must inject a separate backend-only boundary credential when forwarding the request to the control-plane runtime.

That boundary credential is an AegisOps runtime secret, not a Wazuh integration input, and operators must not hand it to Wazuh or use it as a substitute for the reviewed bearer secret.

Wazuh does not expand the sample `${...}` placeholders inside the integration block. Operators must render literal `<hook_url>` and `<api_key>` values with `render-ossec-integration.sh` before loading the reviewed integration into active Wazuh configuration.

The reviewed render helper reads `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE`, materializes `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET` from that mounted file, and then replaces both reviewed placeholders in `ossec.integration.sample.xml` before writing the rendered output.

Do not commit live secrets, enrolled certificates, real IP addresses, or production host paths into this repository.

## 4. Operator Expectations

Operators must treat this package as the reviewed starting point for one single-node Wazuh lab target only.

The approved live path remains `Wazuh -> AegisOps` through the reviewed reverse proxy.

Operators must keep GitHub audit as the only approved first live source family for this slice.

Operators must keep the Wazuh manager, indexer, and dashboard interfaces internal to the lab compose network or another separately reviewed lab access path rather than publishing host ports from this bundle.

Operators must run `render-ossec-integration.sh` in the manager container or another shell where `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE` resolves to the mounted secret path before copying the reviewed integration block into active Wazuh configuration.

Operators must not use these assets to publish the control-plane backend port directly, to insert Shuffle or n8n into the first live path, or to imply that OpenSearch runtime extension work is required for first live success.

Operators must not treat this package as approval for multi-node or production-scale Wazuh, broader source-family rollout, or live response execution.

## 5. Deferred Scope

The following remain explicitly deferred for this asset package:

- multi-node or production-scale Wazuh;
- source families other than GitHub audit;
- direct backend publication that bypasses the reviewed reverse proxy;
- the optional OpenSearch runtime extension;
- thin operator UI work; and
- guarded automation live wiring.

## 6. Reviewable Usage Boundary

These reviewed assets are explicit enough to bootstrap the first live lab substrate target while keeping the Phase 18 slice narrow and reviewable.

Any future change that adds broader source admission, new runtime blockers, production hardening claims, or alternate first live routing must update the governing Phase 18 contract and validation records first.
