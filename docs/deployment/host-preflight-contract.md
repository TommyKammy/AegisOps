# Phase 52.6 Host Preflight Contract

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-1-cli-command-contract.md`, `docs/phase-52-2-smb-single-node-profile-model.md`, `docs/deployment/combined-dependency-matrix.md`, `docs/deployment/compose-generator-contract.md`, `docs/deployment/env-secrets-certs-contract.md`
- **Related Issues**: #1063, #1066, #1069

This contract defines host preflight input and output expectations for the executable first-user stack only. It does not implement the installer, stack startup, live host probing, Wazuh product profiles, Shuffle product profiles, production supportability, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

The host preflight contract gives later setup commands one fail-closed checklist for host prerequisites before the executable first-user stack is started.

The contract covers Docker, Docker Compose, RAM, disk, ports, `vm.max_map_count`, and setup profile validity.

The contract consumes the Phase 52.3 dependency matrix fields in `docs/deployment/combined-dependency-matrix.md` and must not redefine dependency authority outside that matrix.

## 2. Authority Boundary

Host preflight output is setup readiness evidence only.

Docker state, Docker Compose state, RAM, disk, port state, `vm.max_map_count`, generated config, setup profile selection, fixture output, or preflight status is not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.

## 3. Checked Inputs

| Check | Required input | Pass condition | Fail-closed condition |
| --- | --- | --- | --- |
| Docker engine | `AEGISOPS_PREFLIGHT_DOCKER_ENGINE_VERSION`, `AEGISOPS_PREFLIGHT_DOCKER_CONTEXT`, `AEGISOPS_PREFLIGHT_DOCKER_SOCKET_EXPOSURE` | Docker Engine 24 or 25 is present on a reviewed local context with no untrusted socket exposure. | Missing Docker, unsupported major version, remote or rootless profile outside the reviewed package, or untrusted socket exposure fails. |
| Docker Compose | `AEGISOPS_PREFLIGHT_COMPOSE_VERSION`, `AEGISOPS_PREFLIGHT_COMPOSE_FILE`, `AEGISOPS_PREFLIGHT_COMPOSE_ENV_FILE` | Docker Compose plugin v2.24 or newer is present and references reviewed repo-relative or placeholder-backed compose and env files. | Missing Compose, standalone Compose v1, malformed version, or host-local absolute path guidance fails. |
| RAM | `AEGISOPS_PREFLIGHT_HOST_RAM_GB` | At least 16 GB is present for minimum rehearsal; 32 GB remains the recommended first-user target. | Missing RAM signal, nonnumeric RAM, or RAM below 16 GB fails. |
| Disk | `AEGISOPS_PREFLIGHT_HOST_DISK_GB`, `AEGISOPS_PREFLIGHT_HOST_BACKUP_DISK_GB` | At least 250 GB durable disk plus separate backup capacity is present for minimum rehearsal. | Missing disk signal, nonnumeric disk, disk below 250 GB, or backup storage not represented separately fails. |
| Ports | `AEGISOPS_PREFLIGHT_PROXY_PUBLIC_PORTS`, `AEGISOPS_PREFLIGHT_COMPOSE_PUBLISHED_PORTS`, `AEGISOPS_PREFLIGHT_CONTROL_PLANE_PORT`, `AEGISOPS_PREFLIGHT_POSTGRES_PORT` | Only reviewed proxy-public ports are host-published; backend and database ports remain internal. | Port conflict, direct backend publication, direct database publication, malformed port value, or inferred port ownership fails. |
| `vm.max_map_count` | `AEGISOPS_PREFLIGHT_VM_MAX_MAP_COUNT` | Linux hosts report `vm.max_map_count` at or above `262144`; non-Linux hosts may return a documented `skip` with reason. | Missing Linux `vm.max_map_count`, nonnumeric value, or value below `262144` fails. |
| Profile validity | `AEGISOPS_PREFLIGHT_PROFILE`, `AEGISOPS_PREFLIGHT_PROFILE_MODE`, `AEGISOPS_PREFLIGHT_PROFILE_REVISION` | The profile is `smb-single-node`, mode is `demo` or `production-dry-run`, and the profile revision is release-bound. | Missing profile, unknown profile, TODO/sample placeholder, inferred profile name, or floating revision fails. |

## 4. Output States

| State | Meaning | Accepted use |
| --- | --- | --- |
| `pass` | The check satisfied the reviewed input contract. | May contribute readiness evidence for setup. |
| `fail` | The check is missing, malformed, incompatible, conflicting, or untrusted. | Blocks setup until repaired or explicitly retained as a failed prerequisite. |
| `skip` | The check is not applicable to the current reviewed host class and includes a reason. | May appear only for documented platform differences such as non-Linux `vm.max_map_count`. |
| `mocked` | The result came from a fixture or test double, not live host state. | Valid only in fixture expectations and tests; it is not setup readiness evidence. |

Every preflight result must include the check name, state, source, summary, and safe next action. Failed results must not be reported as success. Mocked results must not be promoted to live readiness evidence.

## 5. Fixture Expectations

Fixture expectations live under `docs/deployment/fixtures/host-preflight/`.

| Fixture | Required state | Required failing check |
| --- | --- | --- |
| `valid-pass.json` | `pass` | None |
| `mocked-pass.json` | `mocked` | None |
| `non-linux-vm-max-map-count-skip.json` | `skip` | None |
| `missing-docker.json` | `fail` | Docker engine |
| `missing-compose.json` | `fail` | Docker Compose |
| `bad-ports.json` | `fail` | Ports |
| `low-ram.json` | `fail` | RAM |
| `missing-vm-max-map-count.json` | `fail` | `vm.max_map_count` |
| `invalid-profile.json` | `fail` | Profile validity |

Negative fixtures must fail closed when a missing Docker engine, missing Docker Compose plugin, bad port conflict, low RAM, missing Linux `vm.max_map_count`, or invalid profile is reported as `pass`, `skip`, or `mocked`.

## 6. Dependency Matrix Link

The host preflight contract must consume the Phase 52.3 dependency matrix instead of duplicating product-support truth.

Required references from this contract include `AEGISOPS_PREFLIGHT_DOCKER_ENGINE_VERSION`, `AEGISOPS_PREFLIGHT_COMPOSE_VERSION`, `AEGISOPS_PREFLIGHT_HOST_RAM_GB`, `AEGISOPS_PREFLIGHT_HOST_DISK_GB`, `AEGISOPS_PREFLIGHT_PROXY_PUBLIC_PORTS`, `AEGISOPS_PREFLIGHT_VM_MAX_MAP_COUNT`, and `AEGISOPS_PREFLIGHT_PROFILE`.

Known incompatible versions, missing prerequisites, malformed fields, placeholder-backed credentials, direct backend exposure, raw forwarded-header trust, and inferred scope bindings must fail closed.

## 7. Validation Rules

Validation must fail closed when:

- Docker or Docker Compose coverage is missing;
- RAM, disk, ports, `vm.max_map_count`, or profile validity coverage is missing;
- fixture expectations for missing Docker, missing Compose, bad ports, low RAM, missing `vm.max_map_count`, or invalid profile are missing;
- any negative fixture reports `pass`, `skip`, or `mocked` instead of `fail`;
- `pass`, `fail`, `skip`, and `mocked` output states are not distinguished;
- preflight readiness evidence is described as AegisOps workflow truth;
- placeholder credentials, sample secrets, TODO values, raw forwarded headers, direct backend ports, direct database ports, or inferred profile names are treated as valid; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<compose-file>`, `<runtime-env-file>`, and `<preflight-output>`.

## 8. Forbidden Claims

- Host preflight status is AegisOps workflow truth.
- Docker status is AegisOps workflow truth.
- Docker Compose status is AegisOps workflow truth.
- Port state is AegisOps release truth.
- Mocked preflight output is live readiness evidence.
- Skipped `vm.max_map_count` is valid on Linux.
- Missing Docker reported as success.
- Bad port conflict reported as success.
- Low RAM reported as success.
- Missing `vm.max_map_count` reported as success.
- Invalid profile reported as success.
- This contract implements the installer.
- This contract starts the stack.
- This contract implements Wazuh product profiles.
- This contract implements Shuffle product profiles.

## 9. Validation

Run `bash scripts/verify-phase-52-6-host-preflight-contract.sh`.

Run `bash scripts/test-verify-phase-52-6-host-preflight-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1069 --config <supervisor-config-path>`.

The verifier must fail when the host preflight contract is missing, when checked inputs or output states are incomplete, when fixture expectations are missing or falsely successful, when dependency-matrix linkage is absent, when preflight evidence is treated as workflow truth, or when publishable guidance uses workstation-local absolute paths.

## 10. Non-Goals

- No installer, stack startup, compose generation, profile generation, live host probing, runtime behavior, RC behavior, or GA behavior is implemented here.
- No Wazuh product profile or Shuffle product profile is implemented here.
- No Docker, Docker Compose, RAM, disk, port, `vm.max_map_count`, profile, fixture, generated config, mocked output, skipped check, log text, or operator-facing summary becomes authoritative AegisOps truth.
