# Detector Activation Evidence Handoff Manifest

## 1. Purpose and Boundary

The detector activation evidence handoff is a compact review package for Phase 40 detector activation, disable, and rollback decisions.

The manifest is evidence custody only; AegisOps-owned alert, case, evidence, reconciliation, and release-gate records remain authoritative.

It must not become a compliance archive platform, unlimited detector history system, external ticket authority, or optional-extension prerequisite.

The package keeps rule review evidence, fixture and parser evidence, activation evidence, rollback evidence, alert or case admission sanity, and known limitations visible to operators, maintainers, and auditors without turning detector activation into a parallel archive or workflow authority.

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this detector activation evidence handoff as the bounded detector scope, owner, rollback, disable, expected-volume, false-positive, and known-limitation evidence for pilot entry.

## 2. Manifest Fields

| Field | Required evidence | Authority boundary |
| --- | --- | --- |
| Rule review evidence | Candidate rule identifier, lifecycle state, source-family package, reviewer, rule intent, source scope, expected alert volume, expected benign cases, false-positive review, next-review date, and activation owner. | Rule review evidence gates activation but does not make the detector source authoritative for case or workflow truth. |
| Fixture and parser evidence | Reviewed fixture paths, parser or decoder identity, validation command result, source field coverage, timestamp quality, provenance evidence, and the exact fixture set used for review. | Fixture evidence proves the admitted alert shape only; parser drift or fixture drift blocks activation until refreshed review is recorded. |
| Activation evidence | Activation window, reviewer sign-off, activation owner, disable owner, rollback owner, release-gate evidence record, repository revision, and the AegisOps alert, case, evidence, or reconciliation identifiers that received detector evidence. | Activation is accepted only through AegisOps-owned records and release-gate evidence, not through Wazuh, OpenSearch, GitHub, Entra ID, or ticket status alone. |
| Rollback and disable evidence | Disable reason, rollback reason, restored rule revision, restored fixture set, validation rerun result, operator notification path, follow-up owner, and release-gate evidence record. | Rollback is a non-destructive content, rule-set, fixture, and validation reset path; it does not authorize direct source-side mutation or undocumented hotfixes. |
| Alert or case admission sanity | AegisOps alert, case, evidence, or reconciliation identifiers, admission result, reviewed linkage to the source-family record, and clean-state outcome for failed or rejected paths. | Case admission remains control-plane-owned and must fail closed when provenance, scope, linkage, or snapshot consistency is missing. |
| Known limitations | Deferred detector behavior, unsupported source fields, parser gaps, expected false-positive limits, retention limit, optional-extension non-requirements, and follow-up owner. | Limitations preserve review context without creating an unlimited history system or expanding detector authority. |

## 3. Required Review Questions

- Does the handoff name the exact candidate rule, source-family package, fixture set, validation command result, reviewer, activation owner, disable owner, rollback owner, and next-review date?
- Does the handoff cite AegisOps-owned alert, case, evidence, reconciliation, or release-gate records for activation and rollback evidence?
- Did rule review evidence preserve the intended analytic scope, false-positive expectations, expected alert volume, and known limitations without inferring scope from names or nearby metadata?
- Did fixture and parser evidence prove the reviewed alert shape, timestamp quality, source-family field coverage, and Wazuh provenance used for detector review?
- Did alert or case admission preserve explicit reviewed linkage, fail closed on missing provenance or scope, and leave no orphan record, partial durable write, or half-admitted case after rejected paths?
- Does rollback or disable evidence identify the restored rule revision, restored fixture set, validation rerun result, owner, notification path, and follow-up without approving direct source-side mutation?

## 4. Source-Family Alignment

GitHub audit and Entra ID runbooks must point detector activation review to this manifest before a candidate moves beyond staging review.

Source-family runbooks must keep detector handoff subordinate to AegisOps-owned records. GitHub audit, Entra ID, Wazuh, OpenSearch, and external ticket fields may provide evidence, but they do not own case state, approval state, action state, execution state, reconciliation truth, release readiness, or rollback completion.

If source-family evidence is missing parser coverage, missing provenance, placeholder credentials, inferred tenant or repository linkage, unsigned identity hints, raw forwarded identity, or mixed-snapshot admission evidence, the handoff remains blocked until the prerequisite is supplied or the rejected path is preserved as the reviewed outcome.

## 5. Validation

Run `scripts/verify-detector-activation-evidence-handoff.sh` after changing this manifest, the GitHub audit runbook, the Entra ID runbook, or detector activation candidate evidence.

Focused validation for a handoff package should also include the source-family candidate verifier, the fixture or parser test named by the candidate, and the control-plane case admission sanity check that proves rejected paths leave durable state clean.

## 6. Out of Scope

Unlimited detector history retention, compliance archive platform design, external ticket authority, direct GitHub API actioning, direct Entra ID actioning, optional-extension startup gates, and source-owned workflow truth are out of scope.

This manifest does not require external ticket systems, optional extensions, customer-private credentials, live detector credentials, direct source-side mutation, source-side enforcement, or a long-term detector archive before a reviewed AegisOps handoff can close.
