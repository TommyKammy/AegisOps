# Phase 67 Real-Integration Prerequisite Evaluation

## Direct Verdict

`integration_trial_passed_with_owned_limitations`

GA acceptance: not accepted.

This verdict is limited to one non-production, single-host, real-service trial.
It records demonstrated interoperability and does not authorize production
rollout, autonomous remediation, or a GA claim.

## Evaluation Basis

- Epic: #1414.
- Child issues: #1415, #1416, #1417, and #1418.
- Operator runner:
  `control-plane/deployment/phase-67-integration-lab/run-e2e-trial.sh`.
- Evidence schema:
  `control-plane/deployment/phase-67-integration-lab/e2e/evidence-manifest.schema.json`.
- Publishable redacted packet:
  `control-plane/deployment/phase-67-integration-lab/e2e/sample-evidence.json`.
- Raw service logs, command output, and the full redacted report remain under
  the mode-`0600` local runtime evidence directory and are not committed.

The published packet records trial
`phase67-e2e-20260801T101013Z-3f1ab3cf5906`, captured at
`2026-08-01T10:13:49.959152Z` against repository revision
`afd494452ea85ba4f81844f564190833d2c99fb0` and snapshot
`phase67-snapshot-91d9f7ae646a86cc`. All 15 required journey steps passed on
the dedicated `colima-aegisops-phase67` Docker context.

The evidence packet binds every journey step to one full repository revision,
one rendered Compose digest, one schema digest, one runtime artifact digest,
one set of image digests, and one trial run ID. Service health is recorded only
as subordinate evidence and is never used as workflow truth.

## Demonstrated Capabilities

- The reviewed Colima lab starts Wazuh, AegisOps, Shuffle, PostgreSQL, and the
  HTTPS proxy under one dedicated Compose project and `full` profile.
- One harmless native Wazuh alert crosses the reviewed HTTPS proxy boundary and
  is admitted once into the AegisOps analyst queue.
- Replaying the native Wazuh alert preserves the original AegisOps alert and
  finding identifiers.
- The admitted alert is promoted to a case through the AegisOps service record
  path.
- A requester and a distinct approver are recorded. A denied action request is
  rejected before dispatch and produces zero Shuffle executions.
- The approved low-risk action reaches one reviewed real Shuffle workflow. The
  native execution and receipt identifiers are persisted as subordinate
  evidence.
- AegisOps reconciliation compares the received binding with its authoritative
  action, approval, delegation, and execution records. Shuffle success alone is
  insufficient.
- Replaying the receipt preserves one execution and one reconciliation record.
- Invalid credential, proxy bypass, failed execution, malformed receipt, and
  reconciliation mismatch probes are rejected or contained without an
  authoritative state delta.
- A redacted report is derived from AegisOps records under a repeatable-read
  snapshot.
- A stop/start cycle preserves the alert, case, action, approval, execution, and
  reconciliation records. Non-destructive cleanup stops containers while
  preserving volumes and local evidence.

## Failed Or Unresolved Capabilities

No required Phase 67.4 journey step is recorded as failed or unresolved in the
publishable packet. This does not convert untested production capabilities into
passes. The owned limitations below remain outside the demonstrated boundary.

## Owned Limitations

| Limitation | Owner | Status | Required follow-up |
|---|---|---|---|
| One Apple Silicon host and one Colima profile | AegisOps platform operations | Accepted for this trial | Repeat on the release host class before production rollout |
| One Wazuh rule and one reviewed harmless Shuffle workflow | AegisOps integration engineering | Follow-up required | Expand the reviewed connector and detector matrix without weakening authority checks |
| No production traffic, customer data, HA, scale, or disaster-recovery exercise | AegisOps release owner | Blocking for GA | Execute separately owned production-readiness gates |
| No design-partner acceptance or customer success evidence | AegisOps product and release owners | Blocking for GA | Collect separate pilot evidence under the Phase 51.3 gate contract |

## Follow-Up Issue Policy

This evaluation does not silently close the limitations above. Each limitation
that enters an actual GA plan must be assigned to a separately scoped issue
before that gate can be accepted. Phase 67.4 itself does not invent production
evidence or accept those future issues on behalf of their owners.

## Authority Boundary

AegisOps alert, case, action request, approval decision, action execution,
reconciliation, report, and limitation records remain authoritative. Wazuh
alerts, Shuffle executions, service health, service logs, screenshots, reports,
verifier output, and issue-lint output are evidence inputs only. They cannot
approve, reconcile, close, or accept readiness by themselves.

## Verification

```bash
bash scripts/verify-phase-67-4-real-service-e2e.sh
bash scripts/test-verify-phase-67-4-real-service-e2e.sh
python3 -m unittest control-plane/tests/test_phase67_4_real_service_e2e.py
```

The real-service operator run is deliberately separate from CI because it
requires initialized local substrates and file-bound lab secrets:

```bash
control-plane/deployment/phase-67-integration-lab/run-e2e-trial.sh
```

## Explicit Non-Claims

- This evaluation does not accept the GA gate.
- This evaluation does not prove production readiness, customer success,
  high availability, scale, disaster recovery, or multi-customer tenancy.
- This evaluation does not authorize autonomous or destructive remediation.
- This evaluation does not establish broad SIEM or SOAR parity.
- Passing a verifier, report, dashboard, or external service health check does
  not replace the AegisOps authority records or separate gate ownership.
