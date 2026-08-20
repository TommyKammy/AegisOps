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

Phase 67.3 adds one bounded real execution path:

`approved AegisOps action -> TLS/Bearer Shuffle API -> reviewed local echo -> authenticated receipt polling -> AegisOps reconciliation`

The deterministic adapter remains the default outside this lab. The real
adapter requires an explicit reviewed delegation binding, rejects synthetic
execution and receipt identifiers, and never persists Shuffle's
per-execution authorization token.

Phase 67.4 binds both component paths into one authority-preserving journey:

`native Wazuh alert -> AegisOps admission and case -> distinct human approval -> real Shuffle execution and receipt -> AegisOps reconciliation -> redacted report -> restart proof`

The combined runner requires a clean immutable repository revision and the
`full` profile. It records digest-pinned services, all 15 reviewed journey
steps, denied-action non-dispatch, duplicate delivery behavior, selected
negative probes, persistence after restart, and non-destructive cleanup. The
local raw artifact set retains a Compose digest record bound to the runner-held
revision and Compose values at evidence-build time. The expanded render is
verified from a mode-`0600` temporary file and deleted rather than retaining
interpolated lab credentials. Both startups fail closed if that render changes.
Each retained status capture includes the machine-readable state and health of
the exact reviewed Compose service inventory. Before publication, the builder
reruns the canonical Wazuh and Shuffle semantic validators over the retained
component evidence instead of trusting artifact hashes alone. The snapshot also
binds the real Shuffle worker service, running task container, reviewed digest,
and runtime image ID before and after the reviewed execution. The runner first
proves that no `shuffle-workers` service exists, then binds the created service
ID to the trial with ownership labels as soon as it appears; cleanup refuses to
remove a service unless its ID, labels, and reviewed image still match.
Because Shuffle 2.2.1 creates that service through Docker API v1.40 with both
legacy service-level and task-level network fields, the ownership update
round-trips the complete v1.40 spec and proves that every non-label field is
unchanged. This avoids an implicit network migration or worker task restart.
If startup fails before the first capture completes, cleanup may claim the new
service only after the preflight absence and reviewed Orborus image both match.
Component observation times separately retain the early Wazuh negative probes
and replay as well as the later Shuffle replay and receipt-negative probes, so
the 15-step summary does not flatten their actual chronology. Receipt capture
is timestamped only after the authenticated response is returned and validated.
The operator must interactively approve a challenge bound to the prepared action
through a macOS dialog or exact TTY response; the runner cannot complete from
unattended input. The publishable sample omits raw logs, secret values, private
host paths, and the full local report.

The committed sample is the historical approval-blocked trial captured at
revision `2473b66f5702a38f1d4630c990509bf812a6af7a`. It does not prove the
behavior of the current runner or PR head. Current-revision evidence requires a
new clean-revision trial with an independent human approver.

## Runtime Shape

The default `core` scope starts PostgreSQL, applies the reviewed first-boot migrations plus current runtime migrations through `0015`, starts the AegisOps control plane, and starts the TLS reverse proxy. Later migration checksums are recorded in the same bootstrap metadata table and fail closed on checksum or recorded-schema drift, including reviewed column, constraint type, validated constraint definition, and index definitions. Before service handoff, the lab also hashes the complete final column, constraint, and index catalogs to reprove the definitions introduced by delegated migrations `0001` through `0007` after their reviewed later evolution. Wazuh and Shuffle are opt-in Compose profiles:

| Scope | Services | Host access |
| --- | --- | --- |
| `core` | PostgreSQL, AegisOps, proxy | `https://localhost:18443` |
| `wazuh` | core plus manager, indexer, dashboard | `https://wazuh.localhost:18443` |
| `shuffle` | core plus backend, frontend, Orborus, worker, OpenSearch | `https://shuffle.localhost:18443` |
| `full` | all of the above | the three TLS proxy hostnames above |

Wazuh `4.14.6` is pinned to the reviewed upstream tag commit and arm64 image digests. Shuffle `2.2.1` backend, frontend, Orborus, and worker images are pinned to amd64 digests and run through explicit Colima emulation acceptance. Emulated execution requires both global `binfmt_misc` and the selected QEMU handler to report `enabled`; executable Colima Rosetta is accepted for amd64 instead. PostgreSQL, nginx, Shuffle OpenSearch, the control-plane base image, and the Wazuh certificate generator are also digest-pinned so evidence runs cannot silently change their external substrate. Orborus and the backend mount the selected Colima Docker socket because Shuffle workers are dynamic containers; this grants Docker-daemon authority inside the isolated lab and is not an accepted production topology.

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
binds the selected receipt to that event's generated username and replays the
exact native alert from an exclusive mode-`600` file below the root-protected
Wazuh queue. The replay must deduplicate to the same AegisOps alert. It also
verifies authenticated valid POST rejection over plain HTTP, proxy-bypass,
credential, malformed, unsupported-source, and oversized-payload failures.
Every shared HTTP probe has a five-second connection timeout and a 15-second
total timeout, and the negative probes must leave authoritative analyst-queue
alert state unchanged. The mode-`600` manifest stays below the untracked
runtime evidence directory. Its JSON is built in a cleanup-managed hidden
staging file and validated against the tracked Draft 2020-12 schema before an
atomic rename publishes the completed manifest. The validator additionally
requires RFC 3339 timestamps, matching worktree and running artifact digests,
the same finding identity for the original and replay deliveries, and an
authoritative alert delta recomputed from the captured counts. The trial
rechecks `wazuh-analysisd` and `wazuh-integratord` immediately before capture,
while the manager Compose healthcheck requires integratord throughout startup.
Its schema requires `created` followed by `deduplicated` and represents the
shared AegisOps alert identity once at the manifest boundary, so delivery
records cannot claim different alert IDs. The admitted reviewed
context retains the fixed Wazuh mapping version used to produce the alert.

The regression fixture
`control-plane/tests/fixtures/wazuh/phase67-real-wazuh-ssh-auth-failure-alert.json`
is a sanitized native alert captured from this Wazuh 4.14.6 host trial. It
contains only the synthetic user, RFC 5737 test address, ephemeral lab manager
identity, and native Wazuh metadata; it contains no credential or production
data.

Bootstrap and run the reviewed harmless Shuffle workflow:

```bash
control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh
control-plane/deployment/phase-67-integration-lab/test-shuffle-execution.sh
```

Bootstrap creates the first local Shuffle admin only when the preserved
substrate has no API credential, stores the returned API key in the untracked
mode-`600` secret directory, imports the tracked local-echo workflow, records
its runtime UUID and export digest, and recreates AegisOps with `real_http`
selected. Workflow state is persisted atomically as active ID, pending ID, and
transport mode: fresh initialization has no workflow ID, interrupted creation
resumes the pending ID, and only a validated workflow becomes active. The API
path from AegisOps is TLS-terminated at the proxy and source-address restricted
to the control-plane container. The trial persists a real execution UUID, the
single-execution idempotency count, requested scope, normalized receipt digest,
and AegisOps reconciliation ID; exact receipt replay must return the same
reconciliation record. Orborus uses the project-scoped Compose identity to join
its Swarm overlay and deterministically recreates dynamic Shuffle worker/app
services after an Orborus restart.

After both component trials are initialized, run the complete Phase 67.4
journey from a clean commit:

```bash
control-plane/deployment/phase-67-integration-lab/run-e2e-trial.sh
```

The command starts `full`, reuses the real Wazuh intake boundary, promotes that
exact admitted alert, proves a denied action has no Shuffle execution, records
a separate approved real execution after an authenticated local operator
confirms the displayed approval challenge, reconciles its authenticated
receipt, exports a redacted AegisOps report, restarts the lab, checks
every scoped Wazuh admission/replay reconciliation plus the action-chain record
persistence and exact retained record contents, and stops the lab without deleting volumes
or evidence. The runner records each completed step in
`step-observations.jsonl`; the evidence builder rejects missing, reordered, or
non-chronological observations. After the interactive pause and immediately
before approved dispatch, the runner reloads the denied request, rejection
decision, and authoritative execution count and fails if that proof changed.
The evidence builder binds both the rejected and approved request/decision rows
in the redacted report to their requester, approver, payload hash, target,
lifecycle, and parent record relationships instead of accepting an ID-only
match.
Synthetic receipt failure probes execute
through the real reconciliation service inside a rollback-only transaction,
and the runner verifies both the expected authoritative mismatch reason and
that the successful authoritative execution is unchanged before publishing
evidence. The snapshot ID commits to the revision,
rendered Compose and schema digests, startup runtime digest, reviewed and live
Shuffle workflow digests, workflow API ID, host and Colima identity, selected
profile, and every immutable image reference. The runner captures and validates
the live workflow again immediately before dispatch and rejects any change from
the snapshot. The inventory includes the configured dynamic Shuffle worker
image and the action tag's observed repository digest and runtime image ID
because neither dynamic image is guaranteed to appear in the pre-dispatch
Compose container enumeration. Before startup, the runner proves that no
`shuffle-tools_1-2-0` service exists, then waits for the Shuffle 2.2.1 worker to
auto-create it. The runner derives the actual `shuffle_swarm_executions` overlay
ID from the worker service, validates the exact callback, dynamically allocated
`app-port`, and running task image ID, and observes an unchanged service ID,
version, and non-label specification twice. It then claims ownership labels by
round-tripping the complete service specification and revalidates the runtime
image ID. Cleanup records the exact worker and action IDs and specifications,
stops Compose and Orborus, then removes only those unchanged IDs after rejecting
disappearance or replacement. The restart check removes both stopped services,
re-proves their absence, and separately claims the newly auto-created worker and
action services before continuing. After approval, the runner
also rechecks that action identity and the complete repository snapshot
immediately before dispatch.
Startup, initial health,
restart status, and both workflow exports
are retained with the raw packet. Each status capture must report the exact
control-plane image ID committed by the snapshot; a syntactically valid but
different post-restart image is rejected. Report export is restricted to the exact
record IDs linked to the current trial, so records in preserved volumes from
earlier trials cannot enter the retained report. After cleanup and immediately
before evidence construction, the runner rechecks the captured `HEAD` and the
complete tracked and untracked worktree. The validator binds the reviewed
limitation set to a passing verdict and binds blocked or failed limitations to
their terminal journey step. The historical approval-blocked compatibility path
is limited to the canonical SHA-256 of the one committed packet, so its public
trial ID and revision cannot authorize a fabricated manifest.
The Draft 2020-12 schema separately selects that packet's 11-image profile by
its exact trial, snapshot, revision, and verdict identity; every other packet
must retain the current 13-image full-profile inventory.
Every database-capable invocation of the bind-mounted E2E journey runner uses
the same repository-snapshot guard, including prepare, approved dispatch, and
post-restart verification. Evidence validation accepts both ARM64 and x86_64
host architecture spellings supported by preflight, and requires evaluation
fields to remain null unless the publication step passed; only the exact
fingerprinted historical packet retains its reviewed compatibility exception.
The final validator also binds the reviewed Wazuh rule, each negative probe to
its producing step, and the denial, human-approval, dispatch, evaluation, and
capture timestamps into one causal sequence.
The Wazuh intake harness is retained as a prerequisite subtrial whose trigger,
admission, replay, and boundary-probe timestamps remain verbatim in
`wazuh-output.txt`. Ordered steps 12 and 13 use only the later Shuffle receipt
replay and receipt negative probes, so earlier Wazuh operations are not
relabeled as later journey events. Publication stages the manifest under a
hidden candidate path, then moves the report and raw artifact directory. The
candidate manifest, published report, and complete published artifact set are
validated and rehashed before an atomic no-clobber link exposes the passing
manifest at its canonical path as the last commit point. Failure before that
commit leaves no discoverable passing manifest.

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
bash scripts/verify-phase-67-3-real-shuffle-transport.sh
bash scripts/test-verify-phase-67-3-real-shuffle-transport.sh
python3 -m unittest control-plane.tests.test_phase67_3_real_shuffle_transport
bash scripts/verify-phase-67-4-real-service-e2e.sh
bash scripts/test-verify-phase-67-4-real-service-e2e.sh
python3 -m unittest control-plane.tests.test_phase67_4_real_service_e2e
```

The real-host core smoke boundary requires the selected Colima profile and
explicit Docker context. It proves PostgreSQL-backed AegisOps startup, proxy
health, and access to `/runtime` through the fixed non-production lab identity.
Status evidence records both the repository runtime artifact SHA-256 and the
immutable image ID used by the running control-plane container, so locally
resolved build dependencies remain attributable. The Phase 67.2 Wazuh receipt
and manifest remain subordinate transport evidence. Only AegisOps admission
creates authoritative alert state; the trial does not promote a case or accept
a readiness gate. Reviewed Shuffle execution belongs to Phase 67.3. The
Phase 67.4 packet links those subordinate identifiers to AegisOps records but
still does not accept GA.
