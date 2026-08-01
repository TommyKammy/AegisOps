# Phase 67 Real-Integration Prerequisite Evaluation

## Direct Verdict

`integration_trial_blocked`

GA acceptance: not accepted.

The current trial reached the independent approval boundary and stopped before
Shuffle dispatch because no distinct human approval event was granted. A later
completed trial may emit `integration_trial_passed_with_owned_limitations` only
after that event and every subsequent step are evidenced. Neither verdict
authorizes production rollout, autonomous remediation, or a GA claim.

## Evaluation Basis

- Epic: #1414.
- Child issues: #1415, #1416, #1417, and #1418.
- Operator runner:
  `control-plane/deployment/phase-67-integration-lab/run-e2e-trial.sh`.
- Evidence schema:
  `control-plane/deployment/phase-67-integration-lab/e2e/evidence-manifest.schema.json`.
- Publishable redacted packet:
  `control-plane/deployment/phase-67-integration-lab/e2e/sample-evidence.json`.
- Raw service logs, command output, preparation record, per-run evaluation
  record, and the full redacted report remain under the mode-`0600` local
  runtime evidence directory and are not committed.

The current trial ID, capture time, repository revision, snapshot ID, and
verdict are recorded in the publishable packet. A generated per-run evaluation
record repeats those values and is SHA-256-bound into that packet, so this
policy document cannot be reused as evidence for a later trial by itself.

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
- A requester and an approval challenge bound to the trial, action request, and
  payload are recorded. A denied action request is rejected before dispatch
  and produces zero Shuffle executions.
- Invalid credential and proxy bypass probes are rejected with measured
  authoritative alert counts and zero alert delta.
- Non-destructive cleanup stops containers while preserving volumes and local
  evidence.

## Failed Or Unresolved Capabilities

Step 8 is blocked pending a distinct human approval event. Shuffle dispatch,
receipt capture, real reconciliation negative probes, report export, restart
persistence, and a passing prerequisite evaluation are recorded as `not_run`.
No approval or downstream success is inferred from the prepared action.

## Owned Limitations

| Limitation | Owner | Status | Required follow-up |
|---|---|---|---|
| One Apple Silicon host and one Colima profile | AegisOps platform operations | Accepted for this trial | Repeat on the release host class before production rollout |
| One Wazuh rule and one reviewed harmless Shuffle workflow | AegisOps integration engineering | Follow-up required | Expand the reviewed connector and detector matrix without weakening authority checks |
| No production traffic, customer data, HA, scale, or disaster-recovery exercise | AegisOps release owner | Blocking for GA | Execute separately owned production-readiness gates |
| No design-partner acceptance or customer success evidence | AegisOps product and release owners | Blocking for GA | Collect separate pilot evidence under the Phase 51.3 gate contract |
| Independent human approval not yet granted | AegisOps local operator | Blocking for this trial | Run the reviewed approval ceremony, then repeat steps 8 through 15 |

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
