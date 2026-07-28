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

Phase 67.2 adds one bounded real signal path:

`Wazuh rule 5710 -> custom-aegisops -> TLS proxy -> POST /intake/wazuh -> AegisOps admission`

The proxy remains the only published intake boundary. Caller-supplied trusted
identity headers are cleared, the proxy credential and fixed
`wazuh_detection` source-family attestation are injected from an
untracked read-only include, and Wazuh reads its bearer credential and proxy CA
from mounted files.

## Runtime Shape

The default `core` scope starts PostgreSQL, applies the reviewed first-boot migrations plus current runtime migrations through `0015`, starts the AegisOps control plane, and starts the TLS reverse proxy. Later migration checksums are recorded in the same bootstrap metadata table and fail closed on checksum or recorded-schema drift, including reviewed column, constraint type, validated constraint definition, and index definitions. Before service handoff, the lab also hashes the complete final column, constraint, and index catalogs to reprove the definitions introduced by delegated migrations `0001` through `0007` after their reviewed later evolution. Wazuh and Shuffle are opt-in Compose profiles:

| Scope | Services | Host access |
| --- | --- | --- |
| `core` | PostgreSQL, AegisOps, proxy | `https://localhost:18443` |
| `wazuh` | core plus manager, indexer, dashboard | `https://wazuh.localhost:18443` |
| `shuffle` | core plus backend, frontend, OpenSearch | `https://shuffle.localhost:18443` |
| `full` | all of the above | the three TLS proxy hostnames above |

Wazuh `4.14.6` is pinned to the reviewed upstream tag commit and arm64 image digests. Shuffle `2.2.1` images are pinned to amd64 digests and run through explicit Colima emulation acceptance. Emulated execution requires both global `binfmt_misc` and the selected QEMU handler to report `enabled`; executable Colima Rosetta is accepted for amd64 instead. PostgreSQL, nginx, Shuffle OpenSearch, the control-plane base image, and the Wazuh certificate generator are also digest-pinned so evidence runs cannot silently change their external substrate. Phase 67.1 does not mount the Docker socket or start Orborus, so Shuffle workflow execution remains disabled until Phase 67.3.

## Quick Start

Review `bootstrap.env.sample` before the first run. On this host its defaults select the existing `mac-studio-solo` Colima profile without changing the current Docker context.

```bash
control-plane/deployment/phase-67-integration-lab/init.sh
control-plane/deployment/phase-67-integration-lab/preflight.sh --scope core --write-evidence
control-plane/deployment/phase-67-integration-lab/up.sh core
control-plane/deployment/phase-67-integration-lab/smoke-core.sh
control-plane/deployment/phase-67-integration-lab/down.sh
```

Prepare the pinned Wazuh checkout and generated indexer certificates before a Wazuh or full start. Preparation runs the Wazuh-scoped preflight before its first Docker helper so ARM64 hash generation cannot bypass architecture or emulation acceptance:

```bash
control-plane/deployment/phase-67-integration-lab/prepare-substrates.sh
control-plane/deployment/phase-67-integration-lab/up.sh wazuh
control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh
control-plane/deployment/phase-67-integration-lab/status-wazuh-intake.sh
```

Preparation combines the canonical upstream manager configuration with the
reviewed `wazuh/ossec-integration.xml`, records the result digest, and marks
Wazuh for recreation. The manager installs `custom-aegisops` into its named
integration volume as `root:wazuh` with mode `750`.

`test-wazuh-intake.sh` emits a harmless SSH invalid-user event from reserved
address `192.0.2.67`, waits for a real Wazuh alert and HTTP 202 receipt, then
replays the exact native alert and requires deduplication to the same AegisOps
alert. It also verifies HTTP, proxy-bypass, credential, malformed,
unsupported-source, and oversized-payload failures, and requires zero change
to authoritative analyst-queue alert state across those negative tests. The
mode-`600` manifest stays below the untracked runtime evidence directory. Its
JSON is built in a cleanup-managed hidden staging file and validated against
the tracked Draft 2020-12 schema before an atomic rename publishes the
completed manifest. Its schema requires `created` followed by `deduplicated`
and represents the shared
AegisOps alert identity once at the manifest boundary, so delivery records
cannot claim different alert IDs.

The regression fixture
`control-plane/tests/fixtures/wazuh/phase67-real-wazuh-ssh-auth-failure-alert.json`
is a sanitized native alert captured from this Wazuh 4.14.6 host trial. It
contains only the synthetic user, RFC 5737 test address, ephemeral lab manager
identity, and native Wazuh metadata; it contains no credential or production
data.

Use `status.sh [scope] [--write-evidence]`, `logs.sh [service ...]`, and the bounded tail controlled by `AEGISOPS_LAB_LOG_TAIL` for inspection. Log tails must be integers from 1 through 10000. See [RUNBOOK.md](RUNBOOK.md) for startup, evidence, troubleshooting, and teardown details.

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

The generated proxy certificate is valid for 30 days for `localhost`, internal
DNS name `proxy`, `wazuh.localhost`, `shuffle.localhost`, and `127.0.0.1`.
`init.sh` preserves a valid matching certificate pair, but replaces it when
less than seven days of validity remain or any required DNS or IP SAN is absent
as an exact entry. It also generates mode `0600` nginx includes for `/runtime`
and `/intake/wazuh`. The runtime route uses the fixed reviewed
`phase67-lab-platform-admin` identity and `platform_admin` role only to exercise
the non-production protected-surface boundary; it is not end-user
authentication or a production identity provider. The Wazuh intake include
uses `$remote_addr` instead of trusting a caller-supplied forwarding chain and
clears every protected-surface identity header. Any proxy credential,
certificate, or trust-bundle replacement in an initialized runtime records a
marker that makes the next `up.sh` force service recreation before clearing the
marker. `up.sh` also records the applied tracked proxy-configuration digest and
forces recreation whenever it changes. `prepare-substrates.sh` atomically
copies the generated Wazuh root CA into the proxy trust bundle and marks the
proxy for recreation; bundle validation checks each leaf certificate's
reviewed DNS or admin subject identity as well as validity, chain, and key
pairing, and nginx verifies both the CA and reviewed `wazuh.dashboard`
upstream identity. Existing credential values remain stable; if an initialized
runtime is missing one, `init.sh` fails instead of generating a credential that
no longer matches preserved volume data. The Wazuh dashboard credential
introduced with the proxy-only access path is generated once during migration
and then receives the same missing-credential protection. If `runtime.env` is
absent, initialization also proves that no known project volume remains in the
configured Docker context before generating credentials.

## Verification

Repository-level contract verification does not require Docker:

```bash
bash scripts/verify-phase-67-1-colima-integration-lab.sh
bash scripts/test-verify-phase-67-1-colima-integration-lab.sh
python3 -m unittest control-plane.tests.test_phase67_colima_integration_lab
bash scripts/verify-phase-67-2-real-wazuh-intake.sh
bash scripts/test-verify-phase-67-2-real-wazuh-intake.sh
python3 -m unittest control-plane.tests.test_phase67_2_real_wazuh_intake
```

The real-host core smoke boundary requires the selected Colima profile and
explicit Docker context. It proves PostgreSQL-backed AegisOps startup, proxy
health, and access to `/runtime` through the fixed non-production lab identity.
Status evidence records both the repository runtime artifact SHA-256 and the
immutable image ID used by the running control-plane container, so locally
resolved build dependencies remain attributable. The Phase 67.2 Wazuh receipt
and manifest remain subordinate transport evidence. Only AegisOps admission
creates authoritative alert state; the trial does not promote a case or accept
a readiness gate. Reviewed Shuffle execution belongs to Phase 67.3.
