#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-33-operational-evidence-handoff-pack.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_shared_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook

The Phase 33 operational evidence handoff pack in `docs/deployment/operational-evidence-handoff-pack.md` is the reviewed minimum package for deployment, upgrade, restore, approval, execution, and reconciliation handoff evidence.
EOF

  cat <<'EOF' > "${target}/docs/deployment/single-customer-profile.md"
# Single-Customer Deployment Profile

The Phase 33 operational evidence handoff pack in `docs/deployment/operational-evidence-handoff-pack.md` defines the minimal retained audit package for upgrade, restore, approval, execution, and reconciliation events.
EOF

  cat <<'EOF' > "${target}/docs/deployment/runtime-smoke-bundle.md"
# Phase 33 Runtime Smoke Bundle

The smoke result is one input to the Phase 33 operational evidence handoff pack in `docs/deployment/operational-evidence-handoff-pack.md`; it does not replace approval, execution, restore, or reconciliation record evidence.
EOF
}

write_valid_pack() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/operational-evidence-handoff-pack.md"
# Phase 33 Operational Evidence Retention and Audit Handoff Pack

## 1. Purpose and Boundary

This document defines the Phase 33 operational evidence retention and audit handoff pack for the reviewed single-customer profile.

The handoff pack is a small-team operational package, not a new archive platform, SIEM replacement, or external authority source.

The authoritative record chain remains inside AegisOps reviewed records for approval, evidence, execution, and reconciliation truth.

The pack is anchored to `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, and `docs/deployment/runtime-smoke-bundle.md`.

## 2. Retained Evidence Categories

| Event category | Retained evidence | Authority boundary |
| --- | --- | --- |
| Upgrade | Approved maintenance window, named operator, pre-change backup custody confirmation, selected restore point, before-and-after repository revisions, pre-change and post-change smoke results, bounded upgrade-window logs, and rollback decision. | Handoff evidence only; upgrade success is accepted only when the reviewed runtime checks and AegisOps record chain remain trustworthy. |
| Restore | Triggering reason, selected restore point, backup custody confirmation, repository revision or release identifier, post-restore readiness checks, and approval, evidence, execution, and reconciliation record-chain validation outcome. | Restore evidence supports return-to-service review but does not redefine record truth outside AegisOps. |
| Approval | Customer-scoped approver ownership, approval decision reference, reviewed case or action scope, timeout or rejection reason when applicable, and any break-glass custody note. | Approval truth remains the reviewed AegisOps approval record, not the handoff note. |
| Execution | Action request reference, approved execution surface, dispatch or refusal receipt, bounded executor or substrate receipt when present, and idempotency or correlation evidence needed for review. | Execution truth remains the AegisOps action-execution record and linked receipt, not vendor-local status alone. |
| Reconciliation | Reconciliation record reference, expected outcome, observed outcome, mismatch or terminal marker, reviewer decision, and linked evidence used to close or escalate the outcome. | Reconciliation truth remains the reviewed AegisOps reconciliation record. |

## 3. Operator-Visible Handoff Artifacts

The operator-visible artifacts are the maintenance or review record, runtime smoke result, backup and restore custody note, bounded logs with secrets redacted, readiness and runtime inspection outputs, and reviewed record-chain references.

## 4. Minimal Handoff Package

The minimal handoff package after deployment, upgrade, restore, approval, execution, or reconciliation review contains:

- the reviewed event type and named operator;
- the repository revision or release identifier when the event changes runtime state;
- the customer-scoped scope reference without embedding live customer secrets;
- the required evidence category entries for the event;
- the runtime smoke result when deployment, upgrade, rollback, or handoff readiness is in scope;
- the backup, restore, or rollback custody reference when recovery state is in scope;
- the AegisOps reviewed record identifiers for approval, execution, evidence, or reconciliation when workflow truth is in scope; and
- the next daily queue, health review, restore review, or reconciliation follow-up owner.

## 5. Retention Expectations

Retention is bounded to the reviewed small-team operating need: keep the latest deploy or upgrade handoff, the latest successful restore rehearsal or restore event, open approval, execution, and reconciliation review evidence, and the evidence required for the next daily or weekly operator review.

Older handoff packs may be summarized or superseded after the reviewed follow-up is complete, provided the AegisOps reviewed records and required backup or restore custody evidence remain intact.

## 6. Restore and Reconciliation Alignment

Retention expectations must remain aligned with the Phase 32 restore contract: approval, evidence, execution, and reconciliation records must return cleanly from the selected PostgreSQL-aware restore point before normal operation resumes.

The handoff pack must reference the Phase 33 runtime smoke bundle for deployment, upgrade, rollback, and operator handoff readiness evidence.

If restore, export, readiness, or detail rollup evidence appears to combine mixed snapshots, the handoff must stay blocked until operators can prove one committed state or preserve the refusal as the review outcome.

## 7. Out of Scope

Enterprise SIEM archive design, unlimited retention, new authority sources, broad external archive integration, vendor-specific archive automation, multi-customer evidence warehouses, and raw secret-bearing evidence bundles are out of scope.
EOF
}

commit_fixture() {
  local target="$1"

  git -C "${target}" add .
  git -C "${target}" commit --allow-empty -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_shared_docs "${valid_repo}"
write_valid_pack "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_pack_repo="${workdir}/missing-pack"
create_repo "${missing_pack_repo}"
write_shared_docs "${missing_pack_repo}"
commit_fixture "${missing_pack_repo}"
assert_fails_with "${missing_pack_repo}" "Missing Phase 33 operational evidence handoff pack:"

missing_restore_repo="${workdir}/missing-restore-category"
create_repo "${missing_restore_repo}"
write_shared_docs "${missing_restore_repo}"
write_valid_pack "${missing_restore_repo}"
perl -0pi -e 's/\| Restore \| Triggering reason, selected restore point, backup custody confirmation, repository revision or release identifier, post-restore readiness checks, and approval, evidence, execution, and reconciliation record-chain validation outcome\. \| Restore evidence supports return-to-service review but does not redefine record truth outside AegisOps\. \|\n//' "${missing_restore_repo}/docs/deployment/operational-evidence-handoff-pack.md"
commit_fixture "${missing_restore_repo}"
assert_fails_with "${missing_restore_repo}" "Missing Phase 33 operational evidence handoff pack statement: | Restore | Triggering reason"

missing_minimal_package_repo="${workdir}/missing-minimal-package"
create_repo "${missing_minimal_package_repo}"
write_shared_docs "${missing_minimal_package_repo}"
write_valid_pack "${missing_minimal_package_repo}"
perl -0pi -e 's/- the AegisOps reviewed record identifiers for approval, execution, evidence, or reconciliation when workflow truth is in scope; and\n//' "${missing_minimal_package_repo}/docs/deployment/operational-evidence-handoff-pack.md"
commit_fixture "${missing_minimal_package_repo}"
assert_fails_with "${missing_minimal_package_repo}" "Missing Phase 33 operational evidence handoff pack statement: - the AegisOps reviewed record identifiers"

missing_retention_boundary_repo="${workdir}/missing-retention-boundary"
create_repo "${missing_retention_boundary_repo}"
write_shared_docs "${missing_retention_boundary_repo}"
write_valid_pack "${missing_retention_boundary_repo}"
perl -0pi -e 's/Retention is bounded to the reviewed small-team operating need: keep the latest deploy or upgrade handoff, the latest successful restore rehearsal or restore event, open approval, execution, and reconciliation review evidence, and the evidence required for the next daily or weekly operator review\.\n\n//' "${missing_retention_boundary_repo}/docs/deployment/operational-evidence-handoff-pack.md"
commit_fixture "${missing_retention_boundary_repo}"
assert_fails_with "${missing_retention_boundary_repo}" "Missing Phase 33 operational evidence handoff pack statement: Retention is bounded"

missing_runbook_link_repo="${workdir}/missing-runbook-link"
create_repo "${missing_runbook_link_repo}"
write_shared_docs "${missing_runbook_link_repo}"
write_valid_pack "${missing_runbook_link_repo}"
printf '# AegisOps Runbook\n' > "${missing_runbook_link_repo}/docs/runbook.md"
commit_fixture "${missing_runbook_link_repo}"
assert_fails_with "${missing_runbook_link_repo}" "Missing runbook Phase 33 operational evidence handoff pack link:"

forbidden_archive_repo="${workdir}/forbidden-archive"
create_repo "${forbidden_archive_repo}"
write_shared_docs "${forbidden_archive_repo}"
write_valid_pack "${forbidden_archive_repo}"
printf '\nAn external archive integration is required before approval handoff can close.\n' >> "${forbidden_archive_repo}/docs/deployment/operational-evidence-handoff-pack.md"
commit_fixture "${forbidden_archive_repo}"
assert_fails_with "${forbidden_archive_repo}" "Forbidden Phase 33 operational evidence handoff pack statement: external archive integration is required"

echo "verify-phase-33-operational-evidence-handoff-pack tests passed"
