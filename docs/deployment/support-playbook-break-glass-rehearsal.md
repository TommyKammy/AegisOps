# Support Playbook and Break-Glass Rehearsal

## 1. Purpose and Boundary

This playbook tells maintainers and operators what to inspect when the single-customer pilot degrades without creating emergency authority bypass.

The reviewed operating posture remains business-hours, operator-led, and subordinate to AegisOps authoritative records.

The playbook covers source, detector, coordination, assistant, runtime, rollback, and restore degradation for the reviewed single-customer pilot.

It does not create 24x7 on-call coverage, a customer-specific support contract, direct backend access, direct substrate authority, or emergency authority bypass.

Pilot pause, rollback, and exit decisions must use `docs/deployment/pilot-pause-rollback-exit-criteria.md` so support degradation, break-glass evidence, rollback escalation, unresolved limitations, and next-roadmap input remain reviewed and bounded.

## 2. Common Pilot Failure Modes

| Failure mode | Inspect first | Do not infer |
| --- | --- | --- |
| Source degradation | Source-family evidence, ingest custody, replay or fixture proof, source timestamp, and AegisOps linkage. | Tenant, customer, alert, case, or evidence linkage from names, path shape, comments, or nearby metadata. |
| Detector degradation | Detector activation handoff, candidate rule identifier, fixture evidence, expected volume, false-positive review, disable owner, rollback owner, and next review. | Detector output as case, approval, execution, reconciliation, or rollback truth. |
| Coordination degradation | Zammad boundary, endpoint, reviewed token source, reachability, and explicit AegisOps linkage. | Ticket state, comments, assignee, queue, priority, SLA, escalation, or closure as AegisOps authority. |
| Assistant degradation | Assistant citations, reviewed record ids, linked evidence ids, uncertainty flags, and limited surfaces. | Advisory text as approval, execution, reconciliation, closure, detector activation, or support-coverage authority. |
| Runtime degradation | Reverse-proxy health, readiness, runtime inspection, compose state, bounded logs, env contract, and migration bootstrap. | Direct backend health, optional-extension health, raw forwarded headers, or partial container state as readiness. |
| Rollback degradation | Rollback decision owner, selected restore point, backup custody, before-and-after revisions, smoke result, and clean-state proof. | A clean retry summary as proof that the failed path disappeared. |
| Restore degradation | Backup provenance, restore point, empty target expectation, readiness, record-chain validation, and clean-state proof. | Exception text alone as durable-state proof. |

## 3. Degraded Path Handling

Source handling: inspect the reviewed source-family evidence, ingest custody, replay or fixture proof, source timestamp, and explicit linkage to the AegisOps alert, case, or evidence record before widening source scope.

Detector handling: inspect the detector activation evidence handoff, candidate rule identifier, fixture and parser evidence, expected volume, false-positive review, disable owner, rollback owner, and next-review date before trusting detector output.

Coordination handling: inspect `docs/operations-zammad-live-pilot-boundary.md`, `AEGISOPS_ZAMMAD_BASE_URL`, the reviewed token source reference, endpoint reachability, and explicit AegisOps linkage before treating a ticket pointer as usable coordination context.

Assistant handling: inspect the assistant boundary, citations, reviewed record ids, linked evidence ids, uncertainty flags, and disabled or limited assistant surfaces before relying on an advisory summary.

Runtime handling: inspect the reverse-proxy health, readiness, runtime inspection, compose status, bounded logs, runtime env contract, and migration bootstrap evidence before admitting normal operator use.

Rollback handling: inspect the same-day rollback decision owner, selected restore point, pre-change backup custody, before-and-after repository revision, smoke result, and clean-state evidence before closing the maintenance window.

Restore handling: inspect backup provenance, selected restore point, empty restore target expectation, post-restore readiness, record-chain validation, and clean-state proof before returning to service.

## 4. Break-Glass Custody and Rehearsal

Break-glass custody is a documented recovery exception, not an alternate approval path, permanent operator shortcut, or way to bypass reviewed AegisOps authority.

A break-glass rehearsal must name the trigger, primary custodian, backup custodian, approving reviewer, bounded access window, affected runtime binding, redacted evidence location, rotation follow-up owner, and return-to-normal confirmation.

Missing, placeholder, sample, TODO, unsigned, browser-state, raw forwarded-header, or personal-session credentials keep break-glass blocked until the reviewed custody source is repaired.

Break-glass use must not approve, execute, reconcile, close, activate detectors, mark tickets authoritative, or change rollback acceptance without the reviewed AegisOps record and reviewer path.

After break-glass use, operators must rotate or invalidate the affected secret, capture reload or restart evidence, run the relevant readiness or refusal check, and retain the follow-up owner before normal operation resumes.

## 5. Rollback and Restore Escalation

Rollback and restore escalation must stay cross-linked to `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md`, `docs/deployment/operational-evidence-handoff-pack.md`, and `docs/runbook.md`.

Escalate to rollback when runtime, detector, coordination, assistant, or evidence drift cannot be corrected inside the reviewed maintenance or health-review window without widening scope.

Escalate to restore when authoritative approval, evidence, execution, or reconciliation records are missing, orphaned, partially restored, mixed-snapshot, or no longer attributable to the selected restore point.

Rejected, forbidden, failed, rollback, or restore-failure paths must retain the refusal reason and clean-state proof; it is not enough to record that an exception occurred.

## 6. Evidence Collection Expectations

Evidence collection must remain operator-readable and compact: record the event, named operator, affected path, authoritative AegisOps record ids, repository revision or release identifier, command or inspection output, refusal reason when present, clean-state proof, follow-up owner, and next review.

Use repo-relative commands, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, and `<support-evidence-note.md>`.

Operator-readable support evidence may live as a maintenance note, retained handoff entry, ticket comment, or reviewed runbook entry when it preserves the required fields and links back to authoritative AegisOps records.

Evidence must not include live secrets, DSNs, bootstrap tokens, break-glass tokens, private keys, customer credentials, raw forwarded-header values, unsigned identity hints, or workstation-local absolute paths.

## 7. Verification

Verify this playbook with `scripts/verify-support-playbook-break-glass-rehearsal.sh`.

Negative validation for the verifier is `scripts/test-verify-support-playbook-break-glass-rehearsal.sh`.

Run the verifier after changing this playbook, the runbook, pilot readiness checklist, restore rollback upgrade evidence rehearsal, or operational evidence handoff pack.

## 8. Out of Scope

Formal SLA support, 24x7 support coverage, direct customer-private production access, customer-specific paid support terms, emergency authority bypass, direct backend exposure, direct substrate authority, ticket-system authority, detector-owned workflow truth, assistant-owned workflow truth, and optional-extension launch gates are out of scope.
