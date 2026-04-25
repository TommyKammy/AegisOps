# Single-Customer Release Bundle Inventory

## 1. Manifest Ownership and Version Binding

This document is the repo-owned release bundle manifest for the Phase 38 single-customer launch package after the Phase 37 launch-gate rehearsal.

It defines the reviewed shipped AegisOps package for one customer environment without creating a package-manager distribution, hosted release channel, multi-customer edition, HA topology, or optional-service install bundle.

Manifest owner: IT Operations, Information Systems Department.

Release identifier format: `aegisops-single-customer-<repository-revision>`.

Repository revision binding: the maintained release record must name the exact Git commit or reviewed tag used for the launch window.

Control-plane image tag binding: the default reviewed image tag is `aegisops-control-plane:first-boot` from `control-plane/deployment/first-boot/docker-compose.yml`; if a release retags it, the release record must name both the repository revision and the reviewed image tag.

Bundle handoff owner: the named single-customer operator or maintainer who accepts startup, smoke, restore, rollback, upgrade, and evidence handoff responsibility for the launch window.

This manifest is the first inventory operators read before install, upgrade, rollback, or handoff. It is anchored to `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, `docs/deployment/runtime-smoke-bundle.md`, `docs/deployment/customer-like-rehearsal-environment.md`, `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md`, `docs/deployment/operational-evidence-handoff-pack.md`, and `control-plane/deployment/first-boot/`.

## 2. Required Launch Bundle Inventory

| Bundle entry | Owner | Source path | Release binding | Handoff relevance |
| --- | --- | --- | --- | --- |
| Release bundle manifest | IT Operations, Information Systems Department | `docs/deployment/single-customer-release-bundle-inventory.md` | Required for every `aegisops-single-customer-<repository-revision>` release record | Defines the shipped package boundary, ownership, required entries, optional exclusions, and verifier. |
| Single-customer deployment profile | IT Operations, Information Systems Department | `docs/deployment/single-customer-profile.md` | Bound to the same repository revision as the release bundle manifest | Names the reviewed one-customer operating profile, runtime inputs, boundary, optional-extension posture, upgrade, rollback, and day-2 expectations. |
| First-boot compose artefact | Platform maintainers | `control-plane/deployment/first-boot/docker-compose.yml` | Source of the reviewed control-plane, PostgreSQL, and proxy service composition for the release revision | Starts the shipped first-boot surface and exposes the expected `aegisops-control-plane:first-boot`, `postgres:16.4`, and `nginx:1.27.0` image expectations. |
| Runtime env sample reference | Platform maintainers | `control-plane/deployment/first-boot/bootstrap.env.sample` | Copied into an untracked runtime env file for the named customer environment | Defines required runtime keys and secret-source references without committing live DSNs, tokens, certificates, or customer credentials. |
| First-boot control-plane image recipe | Platform maintainers | `control-plane/deployment/first-boot/Dockerfile` | Built from the same repository revision as the release record unless a reviewed image tag is explicitly named | Defines the control-plane container build context for the release image expectation. |
| First-boot entrypoint and migration bootstrap | Platform maintainers | `control-plane/deployment/first-boot/control-plane-entrypoint.sh` | Bound to the release revision and exercised during startup, upgrade, rollback, and restore restart | Runs runtime-config validation, PostgreSQL reachability proof, and migration bootstrap before readiness is accepted. |
| Reverse-proxy artefacts | Platform maintainers | `proxy/nginx/nginx.conf`, `proxy/nginx/conf.d-first-boot/control-plane.conf` | Bound to the release revision and mounted by the first-boot compose surface | Preserves the reviewed reverse-proxy-first ingress boundary for health, readiness, runtime, protected read-only inspection, and Wazuh-facing intake. |
| Migration artefacts | Control-plane maintainers | `postgres/control-plane/migrations/` | Bound to the same repository revision and copied into the reviewed first-boot image at `/opt/aegisops/postgres-migrations` | Keeps authoritative approval, evidence, execution, reconciliation, runtime, and readiness state aligned with the shipped control-plane schema. |
| Runbook | IT Operations, Information Systems Department | `docs/runbook.md` | Required operator procedure for the release revision | Gives startup, shutdown, restore, rollback, upgrade, secret rotation, daily health review, and handoff steps. |
| Runtime smoke bundle | IT Operations, Information Systems Department | `docs/deployment/runtime-smoke-bundle.md` | Required post-deployment, post-upgrade, post-rollback, and handoff smoke reference | Proves startup status, readiness, protected read-only reachability, queue sanity, and first low-risk action preconditions through the approved boundary. |
| Customer-like rehearsal preflight | IT Operations, Information Systems Department | `docs/deployment/customer-like-rehearsal-environment.md`, `scripts/verify-customer-like-rehearsal-environment.sh` | Required Phase 37 launch-gate precursor for the release revision | Proves the disposable customer-like topology and runtime env prerequisites before the release gate is accepted. |
| Reviewed record-chain rehearsal | Control-plane maintainers | `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`, `control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json` | Required Phase 37 evidence for the release revision | Replays the reviewed alert, case, action request, approval, execution receipt, reconciliation, and handoff chain. |
| Runtime smoke gate script | IT Operations, Information Systems Department | `scripts/run-phase-37-runtime-smoke-gate.sh` | Required executable Phase 37 smoke evidence producer for the release revision | Produces retained smoke evidence and `manifest.md` for launch-gate handoff. |
| Restore, rollback, and upgrade evidence rehearsal | IT Operations, Information Systems Department | `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md`, `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh` | Required release-gate evidence index for the release revision | Connects pre-change backup custody, restore validation, same-day rollback decision, post-upgrade smoke, reviewed-record evidence, and clean-state evidence. |
| Operational evidence handoff pack | IT Operations, Information Systems Department | `docs/deployment/operational-evidence-handoff-pack.md` | Required retained audit handoff reference for the release revision | Defines the compact evidence package operators retain after deployment, upgrade, rollback, restore, approval, execution, reconciliation, and launch handoff. |
| Release bundle inventory verifier | Platform maintainers | `scripts/verify-single-customer-release-bundle-inventory.sh`, `scripts/test-verify-single-customer-release-bundle-inventory.sh` | Required CI and local validation for release-bundle manifest changes | Fails closed when required bundle entries, cross-links, optional-extension exclusions, release bindings, or path-hygiene guarantees drift. |

## 3. Optional and Default-Off Extension Inventory

Optional assistant, ML shadow, endpoint evidence, optional network evidence, external ticketing, OpenSearch, n8n, Shuffle, and isolated-executor paths are subordinate or default-off items only.

They are not mainline release prerequisites, startup prerequisites, readiness gates, smoke prerequisites, upgrade success gates, rollback success gates, restore success gates, or handoff blockers for this single-customer launch package.

If a later reviewed package enables one optional extension, the release record must name the explicit reviewed boundary, owner, source path, runtime binding, and evidence expectation for that extension without widening this manifest's mainline control-plane, PostgreSQL, reverse-proxy, or Wazuh-facing package.

Operators must not infer optional-extension inclusion from repository directory presence, image availability, env sample comments, matching names, nearby notes, or external substrate health.

## 4. Release Record Requirements

For each single-customer launch or reviewed upgrade, the maintained release record must include:

- release identifier in the form `aegisops-single-customer-<repository-revision>`;
- repository revision or reviewed tag;
- control-plane image tag, including `aegisops-control-plane:first-boot` unless an explicit reviewed retag is used;
- first-boot compose path and runtime env sample path;
- reviewed migration artefact revision;
- reverse-proxy artefact revision;
- Phase 37 customer-like rehearsal preflight result;
- Phase 37 reviewed record-chain rehearsal result;
- Phase 37 runtime smoke gate manifest reference;
- restore, rollback, and upgrade release-gate manifest reference;
- operational evidence handoff owner and next review; and
- clean-state validation confirming no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived a failed path.

The release record must use repo-relative paths, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, and `<repository-revision>`. It must not include workstation-local absolute paths, live secrets, DSNs, customer credentials, bootstrap tokens, break-glass tokens, unsigned identity hints, raw forwarded-header values, or placeholder credentials as valid launch evidence.

## 5. Verification

The focused release bundle inventory verifier is:

```sh
scripts/verify-single-customer-release-bundle-inventory.sh
```

The verifier fails closed when the release bundle manifest is missing, required launch bundle entries are absent, required release binding or handoff fields are stale, cross-links from deployment, runbook, runtime smoke, Phase 37 rehearsal, and evidence handoff surfaces are missing, optional extensions are promoted into mainline prerequisites, or publishable guidance uses workstation-local absolute paths.

Negative validation for the verifier is:

```sh
scripts/test-verify-single-customer-release-bundle-inventory.sh
```

## 6. Out of Scope

Package-manager distribution, hosted release channels, direct customer-private production access, zero-downtime deployment, HA, database clustering, multi-customer packaging, vendor-specific backup products, optional-service auto-installation, direct backend exposure, direct browser authority, direct substrate authority, and endpoint, network, assistant, ML, ticketing, OpenSearch, n8n, Shuffle, or isolated-executor paths as launch prerequisites are out of scope.
