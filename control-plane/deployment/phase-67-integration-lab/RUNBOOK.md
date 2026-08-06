# Phase 67.1 Lab Runbook

## Preconditions

1. Review `bootstrap.env.sample`, especially the Colima profile, Docker context, resource minimums, loopback proxy port, subnet, architecture, and emulation acceptance. If using an untracked custom copy, export `AEGISOPS_LAB_BOOTSTRAP_ENV` for the lifetime of the lab shell.
2. Run `init.sh`. It creates an untracked runtime env, mounted AegisOps secrets, Shuffle/Wazuh bootstrap values, a mode `0600` nginx `/runtime` identity include, and a 30-day TLS certificate for the three approved proxy hostnames. Rerunning it reapplies bootstrap settings and renews the certificate when less than seven days remain or a required DNS or IP SAN is absent as an exact entry; changing the proxy identity include or rotating an existing certificate marks the next `up.sh` for forced recreation. An initialized runtime with a missing credential fails closed because preserved volumes retain the original credential. The first rerun after the dashboard-credential migration creates that new credential once and records it in the runtime environment. When `runtime.env` is absent, the configured Docker context must be available and contain none of the known project volumes before initialization can generate new credentials.
3. Run `preflight.sh --scope core --write-evidence`, or select `wazuh`, `shuffle`, or `full` for the intended start. Emulated execution requires global `binfmt_misc` plus the selected QEMU handler to report `enabled`, or an executable Colima Rosetta runtime for amd64. Do not continue past a `BLOCKED:` result.

Preflight is read-only with respect to Colima and Docker. It never starts or reconfigures Colima, changes Docker's active context, removes a container, or creates a Compose resource. With `--write-evidence`, it writes only a timestamped report below the dedicated runtime evidence directory.

## Start

Start the smallest useful boundary first:

```bash
control-plane/deployment/phase-67-integration-lab/up.sh core
control-plane/deployment/phase-67-integration-lab/smoke-core.sh
```

`up.sh` renders the complete Compose model, builds the AegisOps image, waits for service health, and records status evidence. PostgreSQL must become healthy before AegisOps, and AegisOps must become healthy before the proxy. Before service handoff, the control-plane entrypoint hashes the complete final column, constraint, and index catalogs, including the definitions introduced by delegated migrations `0001` through `0007`. The proxy is the only host-published service: use `https://localhost:18443` for AegisOps, `https://wazuh.localhost:18443` for Wazuh, and `https://shuffle.localhost:18443` for Shuffle. The `/runtime` route authenticates as the fixed reviewed `phase67-lab-platform-admin` identity with `platform_admin` role; this is a non-production smoke identity, not end-user authentication. A pending proxy or Wazuh certificate marker, or a change to either tracked nginx configuration file, forces recreation of the selected scope. Marker and applied-configuration state are updated only after Compose succeeds. To keep scoped evidence truthful, `up.sh` rejects a narrower scope while excluded optional-profile services remain running; use `down.sh` before narrowing or switching optional scopes.

For Wazuh, first run `prepare-substrates.sh`. The command clones exactly the configured upstream tag, verifies its commit and tracked working tree, then runs the Wazuh-scoped preflight before its first Docker helper so platform-selected certificate and password-hash containers cannot bypass architecture or emulation acceptance. It validates cached certificate expiry, reviewed leaf identities, chains, and key pairs, regenerates an invalid bundle through the digest-pinned official Wazuh generator in an isolated temporary Docker volume, and updates the upstream `admin` and `kibanaserver` bcrypt entries to match generated lab passwords. Unused upstream demo identities receive a discarded random hash so their published default passwords are not valid. It atomically synchronizes the generated root CA into the proxy trust bundle; nginx verifies the dashboard certificate chain and `wazuh.dashboard` identity. A one-shot security bootstrap reapplies the reviewed internal-user file to a preserved indexer before the dashboard starts. Preparation records the reviewed managed-file digest; `up.sh wazuh` and `up.sh full` recheck the checkout, digest, certificate bundle, and proxy trust copy immediately before startup. Every successful preparation marks the next Wazuh/full start for forced recreation so running services cannot retain an earlier certificate or credential hash. The temporary volume and copy container are removed before the command returns.

```bash
control-plane/deployment/phase-67-integration-lab/prepare-substrates.sh
control-plane/deployment/phase-67-integration-lab/up.sh wazuh
```

Preparation also renders and digests the bounded Phase 67.2 manager
configuration. Startup installs `custom-aegisops` with Wazuh-required
`root:wazuh` ownership and mode `750`. The filter is exactly native rule
`5710`; the lab does not forward the general alert stream.

Run the real Wazuh intake trial:

```bash
control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh
```

The command verifies health and negative boundaries, writes a harmless SSH
invalid-user log using reserved address `192.0.2.67`, waits for the real Wazuh
alert and HTTP 202 AegisOps receipt, replays that native alert, and requires
`deduplicated` with the original AegisOps alert ID. It then requires an
unpromoted `source_system=wazuh` analyst-queue row, proves that the preceding
negative tests produced zero authoritative alert delta, and writes a
mode-`600` manifest below `${AEGISOPS_LAB_EVIDENCE_DIR}`.

The tracked Phase 67.2 regression fixture is a sanitized native capture from
this procedure. It retains the Wazuh native ID, timestamp format, manager
identity, rule, synthetic SSH log, and reserved test address, but no secret or
production data.

Do not replace the bounded test input with a production endpoint, public
address, real username, or customer log.

The tracked bootstrap keeps Shuffle emulation disabled; set
`AEGISOPS_LAB_ALLOW_EMULATION=yes` only in an untracked bootstrap after
accepting the architecture boundary. Phase 67.3 uses the official
Orborus/worker model, so the backend and Orborus receive the selected Colima
Docker socket. Treat both containers as Docker-daemon privileged and keep this
topology isolated and non-production.

```bash
control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh
control-plane/deployment/phase-67-integration-lab/test-shuffle-execution.sh
```

`bootstrap-shuffle.sh` starts the substrate in deterministic mode, registers
the first local admin if needed, stores the returned API key only below the
untracked runtime secret directory, imports the tracked harmless local-echo
workflow, and restarts AegisOps in `real_http` mode. Reruns validate the
preserved credential and workflow instead of creating another workflow.
`runtime.env` stores the workflow transition as one atomic
active-ID/pending-ID/transport-mode state. A first initialization leaves both
IDs empty; if bootstrap stops after creation, the pending ID is resumed on the
next run, and `real_http` is selected only after the preserved workflow passes
validation. The retired placeholder UUID is treated as uninitialized and
removed by the next `init.sh` run.

`test-shuffle-execution.sh` creates one explicitly approved local-sink action,
dispatches it through the authenticated API with at most two attempts, polls
the authenticated execution list, validates every approval, delegation, hash,
workflow, and correlation field, and passes the normalized receipt to AegisOps
reconciliation. An ambiguous timeout is not retried. Exact receipt replay must
return the original reconciliation ID. Failed, missing, malformed, duplicated,
or mismatched receipts fail the trial and do not become accepted
reconciliation truth.

On each Orborus recreation, the lab removes and recreates Shuffle's dynamic
Swarm worker/app services. `ORBORUS_CONTAINER_NAME` uses the configured Compose
project name so Orborus joins the worker overlay without a global
`container_name`. Wait for the bounded Orborus startup window before treating a
queued execution as stalled.

## Complete Phase 67.4 E2E Trial

Run this only after Wazuh substrate preparation and Shuffle bootstrap have
completed, and only from a clean committed revision:

```bash
control-plane/deployment/phase-67-integration-lab/run-e2e-trial.sh
```

The runner uses the `full` profile and one generated trial run ID. It hashes
the repository revision, rendered Compose model, evidence schema, runtime
artifacts, reviewed and live Shuffle workflow digests, workflow API ID, host
and Colima identity, selected profile, and running image identities into one
recomputable snapshot ID before it records step 1. It
starts `full` before capturing runtime identities; step 2 records only the
post-snapshot health status and does not claim to be the startup event. It then
executes the real Wazuh trial, promotes that exact admitted alert to a
case, and prepares a reviewed harmless action. A distinct local operator must
inspect the displayed action request, payload hash, and challenge, then confirm
the macOS operator dialog or type the exact `APPROVE <challenge>` phrase on a
TTY. Only that ceremony persists approval and allows dispatch to real Shuffle.
Immediately before dispatch, the runner reloads the denied request and decision
from PostgreSQL and recounts its executions; any lifecycle change or execution
blocks the trial.
Before snapshot capture, the runner creates the `shuffle-tools_1-2-0` Swarm
service from the reviewed repository digest. The service and its running task
must retain that digest and image ID before approval and again after execution;
the mutable compatibility tag is not the execution reference.
Receipt success is passed through AegisOps reconciliation instead of inferred
from Shuffle state. Receipt failure probes must return the reviewed mismatch
reason and run in a rollback-only transaction;
the trial fails if the authoritative successful execution or record count is
not restored exactly. The retained report uses an explicit record-ID allowlist
for this trial's alert, case, denied and approved requests and decisions,
execution, Wazuh admission/replay reconciliations, and action reconciliation;
records preserved from earlier trials are excluded.

After report export and delivery replay, the runner stops and starts the lab,
checks the persisted action-chain identifiers, every Wazuh admission/replay
reconciliation ID, the one-execution count, and exact equality between the
post-restart authoritative records and the retained report, and
runs `cleanup.sh`. The runner retains a trial-specific raw artifact directory
with mode `0700` and files with mode `0600`, plus the complete redacted report,
below `${AEGISOPS_LAB_EVIDENCE_DIR}`. The manifest records every retained raw
artifact digest and binds a generated evaluation record to the trial, snapshot,
revision, and verdict. The retained `step-observations.jsonl` records the actual
completion time of all 15 steps. The validator requires every completed or
terminal step before `not_run` to be strictly chronological for passed,
blocked, and failed manifests. The prerequisite Wazuh harness retains its own
trigger, admission, replay, and negative-boundary timestamps verbatim in
`wazuh-output.txt`; ordered journey steps 12 and 13 attest only to the later
Shuffle receipt replay and receipt negative probes. The runner rechecks both
`HEAD` and the complete
tracked and untracked worktree after cleanup, immediately before building the
publishable packet. A temporary Compose render is captured before the first
startup, rechecked before both startups and publication, and compared by the
builder with runner-held revision and Compose digest values that are not read
back from staging JSON. Only `compose-config.sha256` is retained; the expanded
render is deleted before publication so interpolated lab credentials are not
kept as evidence. Every verdict
recomputes its snapshot ID from all captured inputs, and each journey identifier
must be present only when its producing step passed. `startup-status.txt`,
`initial-status.txt`, and
`restart-status.txt` retain the exact status captures used by the snapshot,
health, and restart steps. `workflow-snapshot.json` and
`workflow-pre-dispatch.json` retain the semantically validated live exports;
their canonical digests must match before the adapter performs its own live
validation and dispatch. Only a separately reviewed, redacted manifest may be
copied to the tracked sample path. Do not commit the raw command output, report,
service logs, runtime env, or host-local paths.

The evidence validator fails closed on missing or reordered steps, mixed
snapshots, placeholder or synthetic live IDs, same-actor request and approval,
denied dispatch, inferred receipt or reconciliation success, secret exposure,
private host paths, mutable branch references, and a verdict that exceeds the
recorded journey. A passing trial selects
`integration_trial_passed_with_owned_limitations`; it does not accept GA. Its
three reviewed limitation IDs and statuses are mandatory. A current blocked or
failed packet must additionally use the deterministic blocking limitation ID
derived from its terminal step. The historical approval-blocked packet retains
its separately reviewed approval limitation contract only when the complete
canonical packet SHA-256 matches the committed compatibility fingerprint.
Its schema-level 11-image exception is selected only by the exact historical
trial, snapshot, revision, and blocked verdict identity; all current packets
require the 13-image full-profile inventory.
Every retained status capture must also report the exact control-plane image ID
from the snapshot, including after restart.
The snapshot inventory also includes the digest-pinned dynamic Shuffle worker
configured on Orborus plus the observed repository digest and runtime image ID
behind the Shuffle action tag. After operator approval, the runner revalidates
the live workflow and action image, then checks the complete repository
snapshot immediately before dispatch. For publication, report and raw artifacts are moved only
after every destination is checked, and the passing manifest is moved last.
The final manifest path is validated once more after that move and made
read-only before success is declared. Failure before that validation restores
the unpublished packet where possible and never leaves a discoverable passing
manifest with missing references.
The prepare, approved execution, and restart-verification commands all enter
the bind-mounted journey runner through one helper that checks the captured
repository revision and complete worktree immediately before container
execution. The evidence contract accepts the ARM64 and x86_64 host spellings
supported by preflight. A blocked or failed packet must leave every evaluation
field null when the publication step did not pass, apart from the exact
fingerprinted historical compatibility packet.

## Inspect

```bash
control-plane/deployment/phase-67-integration-lab/status.sh full --write-evidence
control-plane/deployment/phase-67-integration-lab/logs.sh
control-plane/deployment/phase-67-integration-lab/logs.sh control-plane proxy
control-plane/deployment/phase-67-integration-lab/status-wazuh-intake.sh
```

Logs are bounded to the latest 200 lines per service by default. Set `AEGISOPS_LAB_LOG_TAIL` to an integer from 1 through 10000 to change the snapshot; `all`, zero, negative, oversized, and follow-mode requests are rejected.

Evidence is stored below `${AEGISOPS_LAB_RUNTIME_ROOT}/evidence`. It may include host and service metadata, so it is mode `0600` and remains untracked. Every header records the Git commit plus the repository runtime state and artifact SHA-256 for the Docker build and repository bind-mount inputs. Status evidence additionally records the immutable image ID of the actual control-plane container, so package resolution differences in locally built images remain attributable and evidence produced from local edits is distinguishable from a clean reviewed checkout.

`status-wazuh-intake.sh` prints Wazuh process health, the latest sanitized
receipt, and the matching analyst-queue row. It never prints the bearer or
proxy secret. Receipts and manifests remain subordinate evidence; they cannot
create a case, approve an action, reconcile execution, close work, or accept a
readiness gate.

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
- no Wazuh intake receipt: inspect bounded `wazuh-manager`, `proxy`, and
  `control-plane` logs, confirm `wazuh-integratord` is running, and rerun
  `prepare-substrates.sh` plus `up.sh wazuh`; do not widen the rule `5710`
  filter.
- Shuffle bootstrap registration rejected: if the preserved Shuffle volume
  already has an administrator but the API-key file is missing, restore the
  original credential or destroy the disposable lab volumes before
  reinitializing; do not generate an unrelated replacement key.
- Shuffle receipt polling timeout or failed execution: inspect bounded
  `shuffle-backend`, `shuffle-orborus`, and dynamic worker logs. Preserve the
  failed evidence and do not mark the action reconciled or rerun dispatch
  manually.
- Shuffle amd64 execution unavailable: preserve the profile settings and use the exact `colima stop` plus `colima start --vm-type vz --vz-rosetta ... --activate=false` command printed by `preflight.sh --scope shuffle`. This host-level change interrupts every workload in that Colima profile, so the lab reports it as a blocker and never applies it automatically. Do not remove the explicit `linux/amd64` platform.
- Phase 67.4 E2E failure: preserve the hidden staging directory printed by the runner, collect bounded `status.sh full --write-evidence` and `logs.sh` output, and record the exact failed step and owner. Do not convert partial component success into a passed E2E verdict.

When a blocker remains, save the relevant scoped preflight, `status.sh ... --write-evidence`, and a bounded `logs.sh` snapshot before changing the lab configuration.
