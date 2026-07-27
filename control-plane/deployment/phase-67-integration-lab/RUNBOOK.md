# Phase 67.1 Lab Runbook

## Preconditions

1. Review `bootstrap.env.sample`, especially the Colima profile, Docker context, resource minimums, loopback proxy port, subnet, architecture, and emulation acceptance. If using an untracked custom copy, export `AEGISOPS_LAB_BOOTSTRAP_ENV` for the lifetime of the lab shell.
2. Run `init.sh`. It creates an untracked runtime env, mounted AegisOps secrets, Shuffle/Wazuh bootstrap values, a mode `0600` nginx `/runtime` identity include, and a 30-day TLS certificate for the three approved proxy hostnames. Rerunning it reapplies bootstrap settings and renews the certificate when less than seven days remain or a required hostname is absent; changing the proxy identity include or rotating an existing certificate marks the next `up.sh` for forced recreation. An initialized runtime with a missing credential fails closed because preserved volumes retain the original credential. The first rerun after the dashboard-credential migration creates that new credential once and records it in the runtime environment. When `runtime.env` is absent, the configured Docker context must be available and contain none of the known project volumes before initialization can generate new credentials.
3. Run `preflight.sh --scope core --write-evidence`, or select `wazuh`, `shuffle`, or `full` for the intended start. Do not continue past a `BLOCKED:` result.

Preflight is read-only with respect to Colima and Docker. It never starts or reconfigures Colima, changes Docker's active context, removes a container, or creates a Compose resource. With `--write-evidence`, it writes only a timestamped report below the dedicated runtime evidence directory.

## Start

Start the smallest useful boundary first:

```bash
control-plane/deployment/phase-67-integration-lab/up.sh core
control-plane/deployment/phase-67-integration-lab/smoke-core.sh
```

`up.sh` renders the complete Compose model, builds the AegisOps image, waits for service health, and records status evidence. PostgreSQL must become healthy before AegisOps, and AegisOps must become healthy before the proxy. The proxy is the only host-published service: use `https://localhost:18443` for AegisOps, `https://wazuh.localhost:18443` for Wazuh, and `https://shuffle.localhost:18443` for Shuffle. The `/runtime` route authenticates as the fixed reviewed `phase67-lab-platform-admin` identity with `platform_admin` role; this is a non-production smoke identity, not end-user authentication. A pending proxy or Wazuh certificate marker forces recreation of the selected scope and is cleared only after Compose succeeds. To keep scoped evidence truthful, `up.sh` rejects a narrower scope while excluded optional-profile services remain running; use `down.sh` before narrowing or switching optional scopes.

For Wazuh, first run `prepare-substrates.sh`. The command clones exactly the configured upstream tag, verifies its commit and tracked working tree, validates cached certificate expiry, chains, and key pairs, regenerates an invalid bundle through the digest-pinned official Wazuh generator in an isolated temporary Docker volume, and updates the upstream `admin` and `kibanaserver` bcrypt entries to match generated lab passwords. Unused upstream demo identities receive a discarded random hash so their published default passwords are not valid. It atomically synchronizes the generated root CA into the proxy trust bundle; nginx verifies the dashboard certificate chain and `wazuh.dashboard` identity. A one-shot security bootstrap reapplies the reviewed internal-user file to a preserved indexer before the dashboard starts. Preparation records the reviewed managed-file digest; `up.sh wazuh` and `up.sh full` recheck the checkout, digest, certificate bundle, and proxy trust copy immediately before startup. Every successful preparation marks the next Wazuh/full start for forced recreation so running services cannot retain an earlier certificate or credential hash. The temporary volume and copy container are removed before the command returns.

```bash
control-plane/deployment/phase-67-integration-lab/prepare-substrates.sh
control-plane/deployment/phase-67-integration-lab/up.sh wazuh
```

Shuffle startup is available for substrate inspection, but workflow execution is intentionally disabled. The tracked bootstrap keeps emulation disabled; set `AEGISOPS_LAB_ALLOW_EMULATION=yes` only in an untracked bootstrap after accepting the architecture boundary. Do not add a Docker socket mount locally. Phase 67.3 must add the reviewed execution boundary.

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

Evidence is stored below `${AEGISOPS_LAB_RUNTIME_ROOT}/evidence`. It may include host and service metadata, so it is mode `0600` and remains untracked. Every header records the Git commit plus the repository runtime state and artifact SHA-256 for the Docker build and repository bind-mount inputs, so evidence produced from local edits is distinguishable from a clean reviewed checkout.

## Stop And Cleanup

```bash
control-plane/deployment/phase-67-integration-lab/down.sh
control-plane/deployment/phase-67-integration-lab/cleanup.sh
```

Both commands preserve PostgreSQL, Wazuh, and Shuffle named volumes, generated secrets, generated certificates, upstream substrate files, and evidence. Before teardown they require every discovered project container, network, and volume to carry both the Phase 67.1 and configured Compose project ownership labels.

Permanent project-volume deletion is a separate, explicit action:

```bash
control-plane/deployment/phase-67-integration-lab/destroy-data.sh \
  --confirm-destroy-phase-67-lab-data
```

That command applies the same ownership proof before deleting only volumes attached to the configured Compose project. It preserves the runtime directory and evidence.

## Blockers

- `Colima profile ... is not running`: start the named profile yourself with the exact command printed by preflight. The lab does not start Colima automatically.
- `Docker context ... does not exist` or socket mismatch: repair/create the dedicated context. Do not use `docker context use` as a workaround.
- resource minimum failure: stop the profile and resize it outside this lab, then rerun preflight.
- proxy host port in use: choose an unused high loopback port in an untracked bootstrap env.
- subnet collision or unusable network/broadcast service address: choose a dedicated subnet and update all service IPv4 variables to unique host addresses.
- owned project network subnet mismatch: stop the lab and remove the existing project network through normal teardown before applying the new subnet.
- initialized runtime credential missing: restore the original credential; if the preserved data is disposable, run the confirmed `destroy-data.sh` path and remove the stale runtime environment before initializing new credentials.
- runtime environment missing while project volumes remain: restore the original `runtime.env` and credentials before running `destroy-data.sh`, or remove only the verified project-owned volumes explicitly; do not allow `init.sh` to generate replacements against preserved data.
- runtime root or runtime environment root mismatch: remove `..` components and symlink escapes; keep the canonical root and generated `runtime.env` below `${HOME}/.local/share/aegisops/`.
- teardown ownership mismatch: stop and inspect the colliding Compose project manually; do not bypass the Phase 67.1 resource-label proof.
- requested scope excludes running services: run `down.sh`, then start the intended narrower or alternate optional scope; do not treat a partial Compose `up` as a scope transition.
- Wazuh substrate missing: run `prepare-substrates.sh`; do not substitute an unreviewed checkout.
- Shuffle amd64 execution unavailable: preserve the profile settings and use the exact `colima stop` plus `colima start --vm-type vz --vz-rosetta ... --activate=false` command printed by `preflight.sh --scope shuffle`. This host-level change interrupts every workload in that Colima profile, so the lab reports it as a blocker and never applies it automatically. Do not remove the explicit `linux/amd64` platform.

When a blocker remains, save the relevant scoped preflight, `status.sh ... --write-evidence`, and a bounded `logs.sh` snapshot before changing the lab configuration.
