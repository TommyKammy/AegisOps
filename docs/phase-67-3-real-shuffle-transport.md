# Phase 67.3 Real Shuffle Transport

- **Status**: Implemented for the isolated non-production Phase 67 lab
- **Date**: 2026-07-29
- **Related issues**: #1414, #1417

Phase 67.3 connects the approved-action boundary to Shuffle 2.2.1 through an
HTTPS, file-backed Bearer-authenticated API client. It retains the deterministic
adapter as the default and selects `real_http` only through the Phase 67 lab
runtime environment.

The reviewed workflow is
`control-plane/deployment/phase-67-integration-lab/shuffle/harmless-local-log-workflow.json`.
It invokes only Shuffle Tools `repeat_back_to_me`; it has no email, ticket,
identity, endpoint, firewall, cloud, or protected-target connector.
Bootstrap reads the persisted workflow back from Shuffle and verifies every
reviewed execution field before enabling `real_http`; server-added metadata is
allowed, but missing or changed reviewed actions, parameters, branches, or
variables fail closed.

Dispatch carries the AegisOps action request, approval decision, delegation,
payload hash, idempotency key, reviewed workflow identity/version, correlation
ID, expected receipt ID, and requested scope in `execution_argument`. A bounded
retry is allowed only when the HTTP transport proves that a connection was not
established. Timeouts, connection resets, and gateway responses are ambiguous
and therefore fail closed without a second POST.
The durable action-execution record enters `dispatching` before the POST. If the
process stops after Shuffle accepts the execution but before AegisOps finalizes
the record, a later request searches Shuffle by the same idempotency key,
requires one exact immutable delegation binding, and finalizes that existing
execution UUID without another POST. Missing, duplicate, or drifted recovery
evidence remains `dispatching` for explicit retry or operator review.

Receipt retrieval uses the authenticated workflow-executions API. The
normalizer selects exactly one UUID execution ID, requires exactly one
execution for the AegisOps idempotency key, rejects malformed or duplicate
results, validates every immutable binding, maps the Shuffle status, and
discards Shuffle's execution authorization token. AegisOps stores the
normalized receipt fingerprint, idempotency count, and requested scope in the
authoritative action execution record. Exact replay returns the existing
reconciliation record.
The trial evidence is validated against the complete tracked JSON Schema before
the additional cross-record and authority checks run.

Shuffle success is subordinate evidence. Reconciliation is recorded only after
the complete AegisOps binding matches. A failed execution marks the action
execution failed and leaves reconciliation mismatched for operator review. No
Shuffle state can approve an action, broaden scope, close a case, or accept a
readiness gate.

Run:

```bash
bash scripts/verify-phase-67-3-real-shuffle-transport.sh
bash scripts/test-verify-phase-67-3-real-shuffle-transport.sh
python3 -m unittest control-plane.tests.test_phase67_3_real_shuffle_transport
control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh
control-plane/deployment/phase-67-integration-lab/test-shuffle-execution.sh
```

The real trial requires explicit amd64 emulation acceptance. Orborus and the
Shuffle backend receive the selected Colima Docker socket to launch dynamic
workers. Orborus uses the project-scoped container identity to join the Swarm
overlay and cleans/recreates only Shuffle dynamic worker services on restart.
This is a lab-only privileged topology and is not production deployment
guidance.
