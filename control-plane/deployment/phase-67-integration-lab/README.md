# Phase 67.1 Colima Integration Lab

This directory is the reviewed non-production scaffold for running AegisOps with real Wazuh and Shuffle containers on a dedicated Colima Docker context.

The lab is intentionally isolated:

- every Docker command names `AEGISOPS_LAB_DOCKER_CONTEXT`; no script changes the global Docker context;
- Compose uses project `aegisops-phase67-lab`, a dedicated bridge network, and project-owned named volumes;
- published ports bind only to `127.0.0.1`;
- generated env, secrets, certificates, upstream substrates, and evidence live outside the repository under `~/.local/share/aegisops/phase-67-integration-lab` by default;
- ordinary `down.sh` and `cleanup.sh` preserve named volumes and evidence;
- only `destroy-data.sh --confirm-destroy-phase-67-lab-data` deletes project volumes.

This is not a production deployment, a GA proof, or broad SIEM/SOAR replacement evidence.

## Runtime Shape

The default `core` scope starts PostgreSQL, applies the reviewed first-boot migrations plus current runtime migrations through `0015`, starts the AegisOps control plane, and starts the TLS reverse proxy. Later migration checksums are recorded in the same bootstrap metadata table and fail closed on checksum or recorded-schema drift. Wazuh and Shuffle are opt-in Compose profiles:

| Scope | Services | Host access |
| --- | --- | --- |
| `core` | PostgreSQL, AegisOps, proxy | `https://localhost:18443` |
| `wazuh` | core plus manager, indexer, dashboard | `https://localhost:18444` |
| `shuffle` | core plus backend, frontend, OpenSearch | `http://localhost:13001` |
| `full` | all of the above | all loopback endpoints |

Wazuh `4.14.6` is pinned to the reviewed upstream tag commit and arm64 image digests. Shuffle `2.2.1` images are pinned to amd64 digests and run through explicit Colima emulation acceptance. Phase 67.1 does not mount the Docker socket or start Orborus, so Shuffle workflow execution remains disabled until Phase 67.3.

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

## Configuration

To override defaults without editing tracked files, copy `bootstrap.env.sample` to an untracked path and set:

```bash
export AEGISOPS_LAB_BOOTSTRAP_ENV=/absolute/path/to/lab-bootstrap.env
control-plane/deployment/phase-67-integration-lab/init.sh
control-plane/deployment/phase-67-integration-lab/preflight.sh --scope core
```

Keep `AEGISOPS_LAB_BOOTSTRAP_ENV` exported for every lab command in that shell. Rerun `init.sh` after changing the untracked bootstrap file; bootstrap values replace the previously generated runtime values while existing secrets remain stable. The reviewed Wazuh and Shuffle versions, commits, and platforms are fixed to the images in `docker-compose.yml` and cannot be overridden. If the subnet changes, update every selected `AEGISOPS_LAB_*_IPV4` value to a unique usable host address in that subnet; an existing owned project network must be removed through normal teardown before its subnet can change. Preflight rejects overlapping Docker networks, network or broadcast addresses, out-of-subnet or duplicate selected service addresses, duplicate selected ports, and host-port ownership conflicts for the selected scope.

The tracked bootstrap defaults `AEGISOPS_LAB_ALLOW_EMULATION=no`. Before selecting `shuffle` or `full`, use an untracked bootstrap and change it to `yes` only after explicitly accepting emulation. Use `preflight.sh --scope full --write-evidence` before a complete lab start. On Apple Silicon, `shuffle` and `full` additionally require the selected Colima profile to expose Rosetta or an x86_64 binfmt handler. On an x86_64 profile, scopes containing ARM64 services require an accepted and registered `qemu-aarch64` handler. Preflight reports the exact profile-preserving Colima restart command when the reviewed Shuffle host capability is absent; it never restarts Colima itself.

The generated proxy certificate is valid for 30 days and only for `localhost` and `127.0.0.1`. `init.sh` preserves a valid matching certificate pair, but replaces it when less than seven days of validity remain. When it rotates an existing pair, it records a marker that makes the next `up.sh` force service recreation before clearing the marker. Existing credential values remain stable; if an initialized runtime is missing one, `init.sh` fails instead of generating a credential that no longer matches preserved volume data.

## Verification

Repository-level contract verification does not require Docker:

```bash
bash scripts/verify-phase-67-1-colima-integration-lab.sh
bash scripts/test-verify-phase-67-1-colima-integration-lab.sh
python3 -m unittest control-plane.tests.test_phase67_colima_integration_lab
```

The real-host core smoke boundary requires the selected Colima profile and explicit Docker context. It proves PostgreSQL-backed AegisOps startup and proxy health only. Wazuh event wiring belongs to Phase 67.2, and reviewed Shuffle execution belongs to Phase 67.3.
