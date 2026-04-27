# Phase 38 Release Handoff Evidence Package

## 1. Purpose and Boundary

This document defines the Phase 38 release handoff evidence package for a single-customer launch or reviewed upgrade.

The package is a bounded repo-owned handoff index, not a new external archive platform, compliance framework, or workflow authority.

AegisOps approval, evidence, execution, reconciliation, readiness, and recovery truth remains in the reviewed AegisOps records and release-gate evidence; downstream tickets, substrate receipts, and operator notes are subordinate context only.

Use this package after the release bundle inventory, install preflight, runtime smoke, and restore, rollback, and upgrade evidence have been assembled for the same release identifier.

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this release handoff package as the reviewed release-readiness and known-limitations evidence source for the pilot entry decision.

Pilot exit-success, exit-no-go, pause, continue, and rollback decisions must point to `docs/deployment/pilot-pause-rollback-exit-criteria.md` instead of treating release handoff alone as pilot success.

## 2. Required Handoff Entries

Every release handoff manifest must include release readiness summary, release bundle identifier, install preflight result, runtime smoke result, backup, restore, rollback, and upgrade rehearsal reference, known limitations, rollback instructions, handoff owner, and next health review.

The release readiness summary must name the launch or upgrade decision, the reviewed repository revision or tag, the single-customer scope, and whether the package is ready, blocked, or accepted with documented limitations.

The known limitations entry must be an explicit reviewed reference for the release window. Absence of a reviewed known-limitations entry blocks handoff because the next operator cannot distinguish "no known limitation" from an unreviewed package.

For pilot launch review, record the known-limitation and retention decision with `docs/deployment/known-limitations-retention-decision-template.md` so `accepted-with-owner`, blocking, rollback, disable, follow-up, and not-reviewed states, plus owners, operator-visible behavior, revisit dates, and bounded retention decisions, are reviewed in one place.

Release notes and known limitations must point to the operator handoff record and the rollback decision record so a launch reviewer can see whether limitations block launch, normal operation, or rollback acceptance.

The rollback instructions entry must point to the reviewed rollback path and the selected restore or configuration reference. It must not rely on memory, external ticket status, or substrate-local naming to infer the recovery target.

## 3. Evidence Sources

Install preflight evidence comes from `scripts/verify-single-customer-install-preflight.sh --env-file <runtime-env-file>`.

Runtime smoke evidence comes from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`.

Restore, rollback, and upgrade evidence comes from `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>`.

The release bundle identifier comes from `docs/deployment/single-customer-release-bundle-inventory.md` and must use the reviewed `aegisops-single-customer-<repository-revision>` format or a reviewed tag-bound equivalent.

The operational handoff reference comes from `docs/deployment/operational-evidence-handoff-pack.md`, but this release package is the launch or upgrade handoff index for the current release window.

## 4. Blocking Outcomes

A failed install preflight, runtime smoke, restore validation, rollback rehearsal, upgrade evidence check, or missing known-limitation review blocks launch handoff and normal operation until the failed prerequisite is fixed or the refusal is retained as the handoff outcome.

If the package records a failed, rejected, forbidden, or restore-failure path, it must include clean-state validation showing that no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived the attempt.

If external ticket records, backup notes, or substrate receipts disagree with AegisOps records or release-gate evidence, keep the AegisOps-owned record as authoritative and repair or annotate the downstream projection.

## 5. Retention and Path Hygiene

The package keeps the current launch or upgrade handoff, the linked release-gate manifest, the latest runtime smoke manifest, and the next health review expectation; it does not promise unlimited retention.

The manifest must use repo-relative paths, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, and `<release-handoff-manifest.md>`.

Retained evidence must not include workstation-local absolute paths, live secrets, DSNs, customer credentials, bootstrap tokens, break-glass tokens, unsigned identity hints, raw forwarded-header values, or placeholder credentials as valid release evidence.

## 6. Verification

Verify a retained release handoff manifest with `scripts/verify-release-handoff-evidence-package.sh --manifest <release-handoff-manifest.md>`.

The verifier fails closed when required handoff entries are missing, placeholder-only, sample, guessed, stale, workstation-local, or when required cross-links to Phase 37 smoke, restore, rollback, upgrade, release bundle, runbook, and operational handoff material are missing.

Negative validation for the verifier is `scripts/test-verify-release-handoff-evidence-package.sh`.

## 7. Out of Scope

External archive platforms, unlimited retention promises, compliance-framework generalization, external ticket lifecycle authority, multi-customer evidence warehouses, direct backend exposure, optional-extension launch gates, and customer-private production access are out of scope.

This package also does not authorize external tickets, downstream substrate lifecycle fields, browser state, raw forwarded headers, optional-extension health, or customer-private production access as release handoff authority.
