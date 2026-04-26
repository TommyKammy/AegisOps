# Single-Customer Pilot Readiness Checklist and Entry Criteria

## 1. Purpose and Boundary

This document defines the reviewed entry checklist for starting one single-customer pilot.

The entry decision is a reviewed go, no-go, or go-with-explicit-limitations decision for one customer environment; it is not a compliance certification, multi-customer rollout approval, SLA commitment, or 24x7 support promise.

This checklist is the reviewed entry decision surface above the release bundle, runtime smoke, detector activation, Zammad coordination, assistant boundary, known-limitations review, retention expectation, and evidence handoff material. It does not provision runtime services, activate detectors by itself, mint Zammad credentials, create customer-private production access, or make external tickets or assistant output authoritative.

Operator training and handoff for the pilot must use `docs/deployment/operator-training-handoff-packet.md` and verify it with `scripts/verify-operator-training-handoff-packet.sh` before treating the pilot operator handoff as ready.

Pilot pause, rollback, and exit decisions must use `docs/deployment/pilot-pause-rollback-exit-criteria.md`; entry readiness alone is not exit-success, rollback acceptance, or permission to continue after a paused or degraded pilot.

## 2. Entry Decision Summary

The pilot may start only when release readiness, runtime smoke, detector activation scope, coordination pilot scope, assistant limitations, data retention, and evidence handoff are reviewed together for the same release identifier.

The decision record must name:

- the reviewed `aegisops-single-customer-<repository-revision>` release identifier or reviewed tag-bound equivalent;
- the single customer environment and named pilot owner without embedding customer secrets;
- the entry decision: go, no-go, or go with explicit limitations;
- the handoff owner and next business health review; and
- the exact evidence records used for release readiness, runtime smoke, detector scope, Zammad coordination, assistant limitations, known limitations, retention, and handoff.

Mixed release identifiers, missing owners, stale smoke evidence, inferred detector scope, unreviewed Zammad credentials, missing assistant limitation language, or absent known-limitations review keep the decision at no-go until the prerequisite is repaired or the refusal is retained as the reviewed outcome.

## 3. Readiness Checklist

Release readiness must be bound to `docs/deployment/single-customer-release-bundle-inventory.md` and `docs/deployment/release-handoff-evidence-package.md` for the same `aegisops-single-customer-<repository-revision>` release identifier.

Runtime smoke must pass through `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` and retain the smoke `manifest.md` as entry evidence.

Detector activation scope must follow `docs/detector-activation-evidence-handoff.md` and name only the reviewed candidate rules, fixture evidence, activation owner, disable owner, rollback owner, expected alert volume, false-positive review, and next-review date accepted for the pilot.

Coordination scope must follow `docs/operations-zammad-live-pilot-boundary.md`; Zammad remains link-first, coordination-only, and non-authoritative for AegisOps case, action, approval, execution, and reconciliation records.

Assistant output remains advisory-only and non-authoritative; it must stay grounded in reviewed control-plane records and linked evidence and must not approve, execute, reconcile, close, or widen pilot scope.

Known limitations must be explicit, reviewed, and tied to the entry decision, including whether each limitation blocks pilot start, allows pilot start with a follow-up owner, or requires rollback or disable evidence.

Data retention for the pilot is bounded to the current release handoff, runtime smoke manifest, detector activation evidence handoff, Zammad coordination reference, assistant limitation note, and next health review expectation; it is not an unlimited archive.

Evidence handoff must name the release handoff record, runtime smoke manifest, detector activation handoff, coordination pilot status, assistant limitation statement, known-limitations review, handoff owner, and next health review.

The support playbook in `docs/deployment/support-playbook-break-glass-rehearsal.md` is the reviewed pilot degradation and break-glass rehearsal reference; pilot entry remains blocked if support expectations would require 24x7 coverage, customer-specific support terms, or emergency authority bypass.

## 4. Required Entry Evidence

| Entry area | Required entry evidence | Blocking condition |
| --- | --- | --- |
| Release readiness | Same release identifier in the release bundle inventory and release handoff package, repository revision or reviewed tag, image tag expectation, install preflight result, restore, rollback, and upgrade evidence reference, and handoff owner. | Missing release identifier, mismatched revision, failed preflight, missing recovery evidence, or missing handoff owner. |
| Runtime smoke | Retained `manifest.md` from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` plus readiness, runtime, protected read-only, queue, and reconciliation read-only evidence. | Failed smoke, stale smoke, direct backend smoke, fake proxy identity, or optional-extension-only readiness. |
| Detector activation | Detector activation evidence handoff for the reviewed candidate set, fixture and parser evidence, owner set, expected volume, false-positive review, disable and rollback evidence, and next-review date. | Inferred source scope, missing provenance, missing owner, missing rollback path, placeholder credentials, or detector status treated as workflow truth. |
| Coordination pilot | Zammad-first coordination scope, reviewed endpoint, credential custody source, available, degraded, or unavailable posture, and explicit AegisOps linkage for any ticket pointer. | Missing `AEGISOPS_ZAMMAD_BASE_URL`, missing reviewed token source, placeholder credential, stale ticket read, mismatched ticket identifier, or ticket state treated as AegisOps authority. |
| Assistant limitations | Advisory-only statement linked to the reviewed assistant boundary and any pilot-specific disabled or limited assistant surfaces. | Assistant output treated as approval, execution, reconciliation, case closure, detector activation, release readiness, or support-coverage authority. |
| Known limitations | Reviewed limitation list with block, accept-with-owner, rollback, disable, or follow-up disposition for each limitation. | Empty or absent limitation review, TODO-only note, sample limitation, no owner, or unclear effect on entry. |
| Evidence handoff and retention | Release handoff record, smoke manifest, detector handoff, coordination status, assistant limitation statement, known-limitations review, handoff owner, and next health review. | Missing evidence owner, mixed snapshots, unlimited retention claim, customer-secret exposure, workstation-local paths, or no next review. |

## 5. Known Limitations, Retention, and Evidence Handoff

Known limitations must preserve the difference between no known blocking limitation and not yet reviewed. A pilot entry decision may record no known blocking limitation only when the limitation review itself is present and names the reviewer, release identifier, scope, and next review.

For accepted limitations, the decision record must name the follow-up owner, expected operator-visible behavior, whether the limitation affects launch, normal operation, rollback acceptance, detector disable, Zammad coordination, assistant output, or evidence handoff, and the review date when the limitation must be revisited.

Retention is bounded to reviewed small-team operating needs. Keep the current pilot entry decision, the release handoff record, runtime smoke manifest, detector activation evidence handoff, Zammad coordination status, assistant limitation statement, known-limitations review, handoff owner, and next health review expectation. Do not promise to retain every raw log line, external ticket field, detector event, assistant prompt, substrate receipt, or historical smoke sample forever.

Evidence handoff remains subordinate to authoritative AegisOps records. External tickets, Wazuh status, source-family output, optional analytics, bounded logs, and operator notes may support the handoff, but they do not become case, action, approval, execution, reconciliation, detector, release, or readiness truth.

## 6. Blocking Outcomes

Missing release readiness, failed runtime smoke, missing detector activation owner, missing disable or rollback owner, missing Zammad credential custody, missing assistant limitation statement, missing known-limitations review, missing evidence handoff owner, or mixed release identifiers blocks pilot entry.

Pilot entry also remains blocked when evidence combines mixed snapshots, uses workstation-local absolute paths, exposes live secrets, relies on placeholder credentials, infers tenant or ticket linkage from names, treats raw forwarded headers as trusted identity, promotes optional extensions into launch gates, or makes external tickets, detector substrates, or assistant output authoritative.

On no-go or failed-entry paths, preserve the refusal reason and clean-state evidence. Do not replace a failed entry attempt with a later success summary unless the failed outcome remains reviewable for the next health review.

## 7. Verification

Verify this checklist with `scripts/verify-pilot-readiness-checklist.sh`.

Negative validation for the verifier is `scripts/test-verify-pilot-readiness-checklist.sh`.

Run the checklist verifier after changing this checklist, the runbook, release bundle inventory, release handoff package, runtime smoke bundle, detector activation evidence handoff, Zammad live pilot boundary, assistant boundary, or operational evidence handoff pack.

## 8. Out of Scope

Formal compliance certification, multi-customer rollout, SLA or 24x7 support promise, external archive platform design, customer-private production access, optional-extension launch gates, direct backend exposure, ticket-system authority, and assistant-owned workflow authority are out of scope.

This checklist does not approve HA, database clustering, hosted release channels, vendor-specific backup products, live source-side mutation, direct detector automation, bidirectional ticket sync, multi-ITSM abstraction, endpoint or network evidence as launch prerequisites, or broad support promises beyond the reviewed business-hours single-customer pilot.
