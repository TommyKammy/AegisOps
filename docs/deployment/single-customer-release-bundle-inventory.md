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

The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` is the Phase 38 handoff index that ties the release bundle identifier, install preflight result, runtime smoke, restore, rollback, upgrade, known limitations, rollback instructions, handoff owner, and next health review to one bounded record.

Pilot entry must use `docs/deployment/pilot-readiness-checklist.md` after the single-customer release bundle inventory is bound to the same `aegisops-single-customer-<repository-revision>` release identifier.

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
| Secret, certificate, and proxy custody checklist | IT Operations, Information Systems Department | Section 2.1 of this manifest, `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, and `control-plane/deployment/first-boot/bootstrap.env.sample` | Required before install, rotation, reload, restore, upgrade, or handoff treats the single-customer package as ready | Names custody owners, source references, fail-closed negative cases, reload and rotation checkpoints, and redacted evidence expectations for secrets, TLS, and the approved proxy boundary. |
| Runbook | IT Operations, Information Systems Department | `docs/runbook.md` | Required operator procedure for the release revision | Gives startup, shutdown, restore, rollback, upgrade, secret rotation, daily health review, and handoff steps. |
| Runtime smoke bundle | IT Operations, Information Systems Department | `docs/deployment/runtime-smoke-bundle.md` | Required post-deployment, post-upgrade, post-rollback, and handoff smoke reference | Proves startup status, readiness, protected read-only reachability, queue sanity, and first low-risk action preconditions through the approved boundary. |
| Customer-like rehearsal preflight | IT Operations, Information Systems Department | `docs/deployment/customer-like-rehearsal-environment.md`, `scripts/verify-customer-like-rehearsal-environment.sh` | Required Phase 37 launch-gate precursor for the release revision | Proves the disposable customer-like topology and runtime env prerequisites before the release gate is accepted. |
| Reviewed record-chain rehearsal | Control-plane maintainers | `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`, `control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json` | Required Phase 37 evidence for the release revision | Replays the reviewed alert, case, action request, approval, execution receipt, reconciliation, and handoff chain. |
| Runtime smoke gate script | IT Operations, Information Systems Department | `scripts/run-phase-37-runtime-smoke-gate.sh` | Required executable Phase 37 smoke evidence producer for the release revision | Produces retained smoke evidence and `manifest.md` for launch-gate handoff. |
| Restore, rollback, and upgrade evidence rehearsal | IT Operations, Information Systems Department | `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md`, `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh` | Required release-gate evidence index for the release revision | Connects pre-change backup custody, restore validation, same-day rollback decision, post-upgrade smoke, reviewed-record evidence, and clean-state evidence. |
| Operational evidence handoff pack | IT Operations, Information Systems Department | `docs/deployment/operational-evidence-handoff-pack.md` | Required retained audit handoff reference for the release revision | Defines the compact evidence package operators retain after deployment, upgrade, rollback, restore, approval, execution, reconciliation, and launch handoff. |
| Release bundle inventory verifier | Platform maintainers | `scripts/verify-single-customer-release-bundle-inventory.sh`, `scripts/test-verify-single-customer-release-bundle-inventory.sh` | Required CI and local validation for release-bundle manifest changes | Fails closed when required bundle entries, cross-links, optional-extension exclusions, release bindings, or path-hygiene guarantees drift. |

### 2.1 Secret, Certificate, and Proxy Custody Checklist

Required custody bindings: PostgreSQL DSN, Wazuh ingest shared secret, Wazuh ingest reverse-proxy secret, protected-surface reverse-proxy secret, admin bootstrap token, break-glass token, ingress TLS certificate chain, ingress TLS private key, trusted proxy CIDR binding, protected-surface proxy service account, and optional OpenBao address, token, token file, KV mount, and secret paths when OpenBao is used.

Each binding must name a custody owner, reviewed source reference, bounded consumer set, rotation or reload checkpoint, and redacted evidence location before release handoff can treat the binding as ready.

Bootstrap and break-glass custody must name primary and backup custodians, document the exception trigger, and prove follow-up rotation before the environment returns to normal operation.

Ingress TLS certificate custody must record certificate-chain owner, private-key custodian, expiry review horizon, reload evidence, and the approved reverse-proxy artefact revision without committing certificate material to Git.

Reverse-proxy custody must prove that TLS termination and trusted-header normalization happen only at the approved ingress boundary, while the control-plane backend, PostgreSQL, OpenBao or mounted secret files, and raw secret material remain off the public front door.

Missing, empty, placeholder, guessed, unsigned, sample, TODO, browser-state, raw forwarded-header, or customer-private custody values are not valid release evidence; install, rotation, reload, restore, upgrade, or handoff must remain failed closed until the reviewed source and owner are present.

Custody change evidence must include the trigger, named operator, custody owner, approved source reference, affected binding, restart or reload result, readiness or refusal result through the reverse proxy, and handoff or operator health review reference.

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

The verifier fails closed when the release bundle manifest is missing, required launch bundle or custody checklist entries are absent, required release binding or handoff fields are stale, cross-links from deployment, runbook, runtime smoke, Phase 37 rehearsal, and evidence handoff surfaces are missing, optional extensions are promoted into mainline prerequisites, direct backend or secret exposure is approved, proxy-boundary custody drifts, fail-closed custody language is removed, or publishable guidance uses workstation-local absolute paths.

Negative validation for the verifier is:

```sh
scripts/test-verify-single-customer-release-bundle-inventory.sh
```

## 6. Out of Scope

Package-manager distribution, hosted release channels, direct customer-private production access, zero-downtime deployment, HA, database clustering, multi-customer packaging, vendor-specific backup products, optional-service auto-installation, direct backend exposure, direct browser authority, direct substrate authority, and endpoint, network, assistant, ML, ticketing, OpenSearch, n8n, Shuffle, or isolated-executor paths as launch prerequisites are out of scope.
