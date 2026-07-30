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
normalized through an explicit allowlist with neutral execution defaults, while
unreviewed properties and missing or changed reviewed actions, parameters,
branches, or variables fail closed.
Bootstrap first discovers an existing exact reviewed workflow before creating
one, and persists a newly returned workflow UUID before the follow-up update so
an interrupted rerun cannot create a duplicate. Every dispatch re-fetches and
revalidates the complete reviewed workflow immediately before its POST.
Transient validation GET failures use the bounded attempt budget without
issuing a POST; authentication failures and definition drift fail immediately.

The dynamic Shuffle Tools app artifact is also reviewed independently from the
workflow's `app_version` label. The lab pulls
`frikky/shuffle@sha256:fd5391cb0af02e92be194a8c4fe67a4221d5fb26f279eaa3f00676b201bf6cb8`
for `linux/arm64`, verifies its repository digest and platform, and only then
tags it as `frikky/shuffle:shuffle-tools_1.2.0` for Orborus. Both the runtime tag
and immutable reference are included in bootstrap and trial evidence.

Dispatch carries the AegisOps action request, approval decision, delegation,
payload hash, idempotency key, reviewed workflow identity/version, correlation
ID, expected receipt ID, and requested scope in `execution_argument`. A bounded
retry is allowed only when the HTTP transport proves that a connection was not
established. Timeouts, connection resets, and gateway responses are ambiguous
and therefore fail closed without a second POST.
The timeout is a total monotonic wall-clock deadline across connection, headers,
and all response-body reads; each read receives only the remaining budget.
The durable action-execution record enters `dispatching` before the POST. If the
process stops after Shuffle accepts the execution but before AegisOps finalizes
the record, a later request searches Shuffle by the same idempotency key,
requires one exact immutable delegation binding, and finalizes that existing
execution UUID without another POST. Missing, duplicate, or drifted recovery
evidence remains `dispatching` for explicit retry or operator review.
Delegation timestamps are canonicalized to UTC before persistence and dispatch,
and JSON scopes are compared with type-strict canonical JSON semantics so
Boolean and numeric substitutions cannot satisfy a reviewed binding.

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
