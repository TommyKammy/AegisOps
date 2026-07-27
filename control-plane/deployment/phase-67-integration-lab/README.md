# Phase 67.1 Colima Integration Lab

This directory is the reviewed non-production scaffold for running AegisOps with real Wazuh and Shuffle containers on a dedicated Colima Docker context.

The lab is intentionally isolated:

- every Docker command names `AEGISOPS_LAB_DOCKER_CONTEXT`; no script changes the global Docker context;
- Compose uses project `aegisops-phase67-lab`, a dedicated bridge network, and project-owned named volumes;
- the only published port is the TLS reverse proxy on `127.0.0.1`;
- generated env, secrets, certificates, upstream substrates, and evidence live outside the repository under `~/.local/share/aegisops/phase-67-integration-lab` by default;
- ordinary `down.sh` and `cleanup.sh` preserve named volumes and evidence;
- only `destroy-data.sh --confirm-destroy-phase-67-lab-data` deletes project volumes.

This is not a production deployment, a GA proof, or broad SIEM/SOAR replacement evidence.

## Runtime Shape

The default `core` scope starts PostgreSQL, applies the reviewed first-boot migrations plus current runtime migrations through `0015`, starts the AegisOps control plane, and starts the TLS reverse proxy. Later migration checksums are recorded in the same bootstrap metadata table and fail closed on checksum or recorded-schema drift, including reviewed column, constraint type, validated constraint definition, and index definitions. Wazuh and Shuffle are opt-in Compose profiles:

| Scope | Services | Host access |
| --- | --- | --- |
| `core` | PostgreSQL, AegisOps, proxy | `https://localhost:18443` |
| `wazuh` | core plus manager, indexer, dashboard | `https://wazuh.localhost:18443` |
| `shuffle` | core plus backend, frontend, OpenSearch | `https://shuffle.localhost:18443` |
| `full` | all of the above | the three TLS proxy hostnames above |

Wazuh `4.14.6` is pinned to the reviewed upstream tag commit and arm64 image digests. Shuffle `2.2.1` images are pinned to amd64 digests and run through explicit Colima emulation acceptance. PostgreSQL, nginx, Shuffle OpenSearch, the control-plane base image, and the Wazuh certificate generator are also digest-pinned so evidence runs cannot silently change their external substrate. Phase 67.1 does not mount the Docker socket or start Orborus, so Shuffle workflow execution remains disabled until Phase 67.3.

## Quick Start

Review `bootstrap.env.sample` before the first run. On this host its defaults select the existing `mac-studio-solo` Colima profile without changing the current Docker context.

```bash
control-plane/deployment/phase-67-integration-lab/init.sh
control-plane/deployment/phase-67-integration-lab/preflight.sh --scope core --write-evidence
control-plane/deployment/phase-67-integration-lab/up.sh core
control-plane/deployment/phase-67-integration-lab/smoke-core.sh
control-plane/deployment/phase-67-integration-lab/down.sh
```

Prepare the pinned Wazuh checkout and generated indexer certificates before a Wazuh or full start:

```bash
control-plane/deployment/phase-67-integration-lab/prepare-substrates.sh
control-plane/deployment/phase-67-integration-lab/up.sh wazuh
```

Use `status.sh [scope] [--write-evidence]`, `logs.sh [service ...]`, and the bounded tail controlled by `AEGISOPS_LAB_LOG_TAIL` for inspection. See [RUNBOOK.md](RUNBOOK.md) for startup, evidence, troubleshooting, and teardown details.

`up.sh` will not represent a narrower scope while services from another optional profile remain running. Run `down.sh` before changing from `full` to `core`, `wazuh`, or `shuffle`, or when switching directly between the two optional scopes.

## Configuration

To override defaults without editing tracked files, copy `bootstrap.env.sample` to an untracked path and set:

```bash
export AEGISOPS_LAB_BOOTSTRAP_ENV=/absolute/path/to/lab-bootstrap.env
control-plane/deployment/phase-67-integration-lab/init.sh
control-plane/deployment/phase-67-integration-lab/preflight.sh --scope core
```

Keep `AEGISOPS_LAB_BOOTSTRAP_ENV` exported for every lab command in that shell. Rerun `init.sh` after changing the untracked bootstrap file; bootstrap values replace the previously generated runtime values while existing secrets remain stable. The canonical runtime root must remain below `${HOME}/.local/share/aegisops/`, and `runtime.env` is fixed inside that root. The reviewed Wazuh and Shuffle versions, commits, and platforms are fixed to the images in `docker-compose.yml` and cannot be overridden. If the subnet changes, update every selected `AEGISOPS_LAB_*_IPV4` value to a unique usable host address in that subnet; an existing owned project network must be removed through normal teardown before its subnet can change. Preflight rejects overlapping Docker networks, network or broadcast addresses, out-of-subnet or duplicate selected service addresses, and proxy-port ownership conflicts. Wazuh and Shuffle remain internal-only services; their user interfaces are selected by the `wazuh.localhost` and `shuffle.localhost` proxy hostnames.

The tracked bootstrap defaults `AEGISOPS_LAB_ALLOW_EMULATION=no`. Before selecting `shuffle` or `full`, use an untracked bootstrap and change it to `yes` only after explicitly accepting emulation. Use `preflight.sh --scope full --write-evidence` before a complete lab start. On Apple Silicon, `shuffle` and `full` additionally require the selected Colima profile to expose Rosetta or an x86_64 binfmt handler. On an x86_64 profile, scopes containing ARM64 services require an accepted and registered `qemu-aarch64` handler. Preflight reports the exact profile-preserving Colima restart command when the reviewed Shuffle host capability is absent; it never restarts Colima itself.

The generated proxy certificate is valid for 30 days for `localhost`, `wazuh.localhost`, `shuffle.localhost`, and `127.0.0.1`. `init.sh` preserves a valid matching certificate pair, but replaces it when less than seven days of validity remain or a required proxy hostname is absent. It also generates a mode `0600` nginx include for `/runtime` from the protected-surface proxy secret. That route uses the fixed reviewed `phase67-lab-platform-admin` identity and `platform_admin` role only to exercise the non-production protected-surface boundary; it is not end-user authentication or a production identity provider. Any proxy credential, certificate, or trust-bundle replacement in an initialized runtime records a marker that makes the next `up.sh` force service recreation before clearing the marker. `prepare-substrates.sh` atomically copies the generated Wazuh root CA into the proxy trust bundle and marks the proxy for recreation; nginx verifies both that CA and the reviewed `wazuh.dashboard` upstream identity. Existing credential values remain stable; if an initialized runtime is missing one, `init.sh` fails instead of generating a credential that no longer matches preserved volume data. The Wazuh dashboard credential introduced with the proxy-only access path is generated once during migration and then receives the same missing-credential protection. If `runtime.env` is absent, initialization also proves that no known project volume remains in the configured Docker context before generating credentials.

## Verification

Repository-level contract verification does not require Docker:

```bash
bash scripts/verify-phase-67-1-colima-integration-lab.sh
bash scripts/test-verify-phase-67-1-colima-integration-lab.sh
python3 -m unittest control-plane.tests.test_phase67_colima_integration_lab
```

The real-host core smoke boundary requires the selected Colima profile and explicit Docker context. It proves PostgreSQL-backed AegisOps startup, proxy health, and access to `/runtime` through the fixed non-production lab identity. Wazuh event wiring belongs to Phase 67.2, and reviewed Shuffle execution belongs to Phase 67.3.
