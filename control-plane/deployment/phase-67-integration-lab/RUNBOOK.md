# Phase 67.1 Lab Runbook

## Preconditions

1. Review `bootstrap.env.sample`, especially the Colima profile, Docker context, resource minimums, loopback ports, subnet, architecture, and emulation acceptance.
2. Run `init.sh`. It creates an untracked runtime env, mounted AegisOps secrets, Shuffle/Wazuh bootstrap values, and a 30-day localhost TLS certificate.
3. Run `preflight.sh --scope core --write-evidence`, or select `wazuh`, `shuffle`, or `full` for the intended start. Do not continue past a `BLOCKED:` result.

Preflight is read-only with respect to Colima and Docker. It never starts or reconfigures Colima, changes Docker's active context, removes a container, or creates a Compose resource. With `--write-evidence`, it writes only a timestamped report below the dedicated runtime evidence directory.

## Start

Start the smallest useful boundary first:

```bash
control-plane/deployment/phase-67-integration-lab/up.sh core
control-plane/deployment/phase-67-integration-lab/smoke-core.sh
```

`up.sh` renders the complete Compose model, builds the AegisOps image, waits for service health, and records status evidence. PostgreSQL must become healthy before AegisOps, and AegisOps must become healthy before the proxy.

For Wazuh, first run `prepare-substrates.sh`. The command clones exactly the configured upstream tag, verifies its commit, generates indexer certificates through the official Wazuh generator in an isolated temporary Docker volume, verifies the complete certificate set, and updates the upstream `admin` bcrypt entry to match the generated lab password. The temporary volume and copy container are removed before the command returns.

```bash
control-plane/deployment/phase-67-integration-lab/prepare-substrates.sh
control-plane/deployment/phase-67-integration-lab/up.sh wazuh
```

Shuffle startup is available for substrate inspection, but workflow execution is intentionally disabled. Do not add a Docker socket mount locally. Phase 67.3 must add the reviewed execution boundary.

```bash
control-plane/deployment/phase-67-integration-lab/up.sh shuffle
```

## Inspect

```bash
control-plane/deployment/phase-67-integration-lab/status.sh full --write-evidence
control-plane/deployment/phase-67-integration-lab/logs.sh
control-plane/deployment/phase-67-integration-lab/logs.sh control-plane proxy
```

Logs are bounded to the latest 200 lines per service by default. Increase the snapshot with `AEGISOPS_LAB_LOG_TAIL`; unbounded follow mode is rejected.

Evidence is stored below `${AEGISOPS_LAB_RUNTIME_ROOT}/evidence`. It may include host and service metadata, so it is mode `0600` and remains untracked.

## Stop And Cleanup

```bash
control-plane/deployment/phase-67-integration-lab/down.sh
control-plane/deployment/phase-67-integration-lab/cleanup.sh
```

Both commands preserve PostgreSQL, Wazuh, and Shuffle named volumes, generated secrets, generated certificates, upstream substrate files, and evidence. They do not affect containers, networks, or volumes outside the dedicated Compose project.

Permanent project-volume deletion is a separate, explicit action:

```bash
control-plane/deployment/phase-67-integration-lab/destroy-data.sh \
  --confirm-destroy-phase-67-lab-data
```

That command deletes only volumes attached to the configured Compose project. It preserves the runtime directory and evidence.

## Blockers

- `Colima profile ... is not running`: start the named profile yourself with the exact command printed by preflight. The lab does not start Colima automatically.
- `Docker context ... does not exist` or socket mismatch: repair/create the dedicated context. Do not use `docker context use` as a workaround.
- resource minimum failure: stop the profile and resize it outside this lab, then rerun preflight.
- host port in use: choose unused high loopback ports in an untracked bootstrap env.
- subnet collision: choose a dedicated subnet and update all service IPv4 variables consistently.
- Wazuh substrate missing: run `prepare-substrates.sh`; do not substitute an unreviewed checkout.
- Shuffle amd64 execution unavailable: preserve the profile settings and use the exact `colima stop` plus `colima start --vm-type vz --vz-rosetta ... --activate=false` command printed by `preflight.sh --scope shuffle`. This host-level change interrupts every workload in that Colima profile, so the lab reports it as a blocker and never applies it automatically. Do not remove the explicit `linux/amd64` platform.

When a blocker remains, save the relevant scoped preflight, `status.sh ... --write-evidence`, and a bounded `logs.sh` snapshot before changing the lab configuration.
