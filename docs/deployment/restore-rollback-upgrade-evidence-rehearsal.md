# Phase 37 Restore Rollback Upgrade Evidence Rehearsal

## 1. Purpose and Boundary

This document defines the Phase 37 release-gate rehearsal for pre-change backup capture, restore validation, same-day rollback decision evidence, post-upgrade smoke, and retained handoff evidence.

The rehearsal is anchored to `docs/deployment/single-customer-release-bundle-inventory.md`, `docs/runbook.md`, `docs/deployment/customer-like-rehearsal-environment.md`, `docs/deployment/runtime-smoke-bundle.md`, and `docs/deployment/operational-evidence-handoff-pack.md`.

The Phase 38 release bundle inventory in `docs/deployment/single-customer-release-bundle-inventory.md` uses this rehearsal as the required release-gate evidence index for restore, rollback, upgrade, smoke, reviewed-record, and clean-state handoff.

The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` consumes the verified restore, rollback, and upgrade release-gate manifest as the authoritative recovery evidence reference for the handoff window.

The release gate proves that backup, restore, rollback, upgrade, smoke, and reviewed-record evidence stay explainable against the AegisOps authoritative record chain. It does not create a vendor backup integration, zero-downtime promise, HA design, cluster failover plan, or multi-customer operating model.

## 2. Prerequisites

Before the rehearsal starts, operators must have:

- an approved maintenance or rehearsal window and a named operator;
- the reviewed repository revision or release identifier before the change;
- a PostgreSQL-aware pre-change backup custody record;
- a reviewed configuration backup or runtime env export reference that does not include live secret values;
- the restore target and restore point selected for same-day rollback;
- the seeded reviewed record-chain rehearsal result from `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`;
- the runtime smoke gate output from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`; and
- a retained release-gate manifest path such as `<release-gate-manifest.md>`.

Missing backup custody, restore target, rollback decision owner, smoke manifest, or reviewed record-chain evidence blocks the release gate until the prerequisite is supplied. Operators must not substitute guessed scope, placeholder credentials, raw forwarded headers, optional-extension health, VM snapshot existence, or substrate-local status for these prerequisites.

## 3. Rehearsal Flow

The reviewed release-gate sequence is:

1. Capture the pre-change readiness, runtime, compose status, bounded logs, repository revision, and backup custody reference.
2. Record the selected restore point and restore target before any upgrade or rollback step begins.
3. Rehearse restore against the reviewed recovery target and validate approval, evidence, execution, and reconciliation records against the reviewed record chain.
4. Record the same-day rollback decision, including whether rollback was not needed or which restore point and configuration revision were used.
5. Apply the reviewed upgrade through the repo-owned first-boot path without direct backend exposure, HA choreography, cluster failover, or optional-extension prerequisites.
6. Run the Phase 37 runtime smoke gate after restore, rollback, or upgrade where feasible and retain its `manifest.md`.
7. Assemble the release-gate manifest and verify it with `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>`.

The restored, rolled-back, or upgraded environment may return to operator use only when readiness, runtime inspection, smoke output, and reviewed record-chain validation describe one committed state.

## 4. Retained Manifest

The retained manifest is the handoff index for the release gate. It must include:

- rehearsal owner and maintenance window;
- pre-change backup custody and selected restore point;
- restore target and restore validation result;
- same-day rollback decision and rollback evidence;
- upgrade revision and post-upgrade evidence;
- runtime smoke manifest reference;
- reviewed record-chain evidence reference;
- clean-state validation confirming no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived a failed path; and
- handoff owner and next review.

The manifest must use repo-relative commands, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, and `<release-gate-manifest.md>`. It must not include workstation-local absolute paths, live secrets, DSNs, bootstrap tokens, break-glass tokens, unsigned identity hints, raw forwarded-header values, or customer-private credentials.

## 5. Fail-Closed Validation

The focused release-gate verifier is:

```sh
scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>
```

The verifier fails closed when the rehearsal document is missing, required cross-links are missing, a retained manifest omits backup, restore, rollback, upgrade, smoke, reviewed-record, or clean-state evidence, placeholder values remain, or publishable guidance uses workstation-local absolute paths.

Rejected, forbidden, failed, or restore-failure paths must preserve the refusal reason and prove durable state remained clean. It is not enough to prove only that an error occurred.

## 6. Out of Scope

Zero-downtime deployment, HA, database clustering, vendor-specific backup product integration, direct backend exposure, optional-extension startup or upgrade gates, multi-customer evidence warehouses, and customer-private production access are out of scope.
