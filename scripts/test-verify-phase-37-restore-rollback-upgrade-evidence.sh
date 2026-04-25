#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment" "${target}/scripts"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_shared_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook

The Phase 37 restore, rollback, and upgrade evidence rehearsal in `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md` is the reviewed release-gate path for tying pre-change backup custody, restore validation, rollback decision evidence, post-upgrade smoke, and retained handoff evidence together.
EOF

  cat <<'EOF' > "${target}/docs/deployment/customer-like-rehearsal-environment.md"
# Customer-Like Rehearsal Environment

Assemble and verify the restore, rollback, and upgrade release-gate manifest with `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>` before handoff closes.
EOF

  cat <<'EOF' > "${target}/docs/deployment/runtime-smoke-bundle.md"
# Phase 33 Runtime Smoke Bundle

For restore, rollback, and upgrade release-gate rehearsal, the smoke manifest is one referenced artifact in the retained release-gate manifest verified by `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>`.
EOF

  cat <<'EOF' > "${target}/docs/deployment/operational-evidence-handoff-pack.md"
# Phase 33 Operational Evidence Retention and Audit Handoff Pack

For Phase 37 restore, rollback, and upgrade rehearsal, retain the release-gate manifest verified by `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>` so backup, restore, rollback, upgrade, smoke, reviewed-record, and clean-state evidence remain linked in one handoff index.
EOF

  cat <<'EOF' > "${target}/scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh"
#!/usr/bin/env bash
exit 0
EOF

  cat <<'EOF' > "${target}/scripts/run-phase-37-runtime-smoke-gate.sh"
#!/usr/bin/env bash
exit 0
EOF

  chmod +x "${target}/scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh" "${target}/scripts/run-phase-37-runtime-smoke-gate.sh"
}

write_valid_doc() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
# Phase 37 Restore Rollback Upgrade Evidence Rehearsal

## 1. Purpose and Boundary

This document defines the Phase 37 release-gate rehearsal for pre-change backup capture, restore validation, same-day rollback decision evidence, post-upgrade smoke, and retained handoff evidence.

The rehearsal is anchored to `docs/runbook.md`, `docs/deployment/customer-like-rehearsal-environment.md`, `docs/deployment/runtime-smoke-bundle.md`, and `docs/deployment/operational-evidence-handoff-pack.md`.

The release gate proves that backup, restore, rollback, upgrade, smoke, and reviewed-record evidence stay explainable against the AegisOps authoritative record chain.

## 2. Prerequisites

- a PostgreSQL-aware pre-change backup custody record;
- the restore target and restore point selected for same-day rollback;
- the seeded reviewed record-chain rehearsal result from `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`;
- the runtime smoke gate output from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`; and

Missing backup custody, restore target, rollback decision owner, smoke manifest, or reviewed record-chain evidence blocks the release gate until the prerequisite is supplied.

## 3. Rehearsal Flow

Rehearse restore against the reviewed recovery target and validate approval, evidence, execution, and reconciliation records against the reviewed record chain.

Record the same-day rollback decision, including whether rollback was not needed or which restore point and configuration revision were used.

Run the Phase 37 runtime smoke gate after restore, rollback, or upgrade where feasible and retain its `manifest.md`.

Assemble the release-gate manifest and verify it with `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>`.

## 4. Retained Manifest

The retained manifest is the handoff index for the release gate.

clean-state validation confirming no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived a failed path

The manifest must use repo-relative commands, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, and `<release-gate-manifest.md>`.

## 5. Fail-Closed Validation

The verifier fails closed when the rehearsal document is missing, required cross-links are missing, a retained manifest omits backup, restore, rollback, upgrade, smoke, reviewed-record, or clean-state evidence, placeholder values remain, or publishable guidance uses workstation-local absolute paths.

## 6. Out of Scope

Zero-downtime deployment, HA, database clustering, vendor-specific backup product integration, direct backend exposure, optional-extension startup or upgrade gates, multi-customer evidence warehouses, and customer-private production access are out of scope.
EOF
}

write_valid_manifest() {
  local path="$1"

  cat <<'EOF' > "${path}"
# Phase 37 Restore Rollback Upgrade Evidence Manifest

Rehearsal owner: release-gate-operator
Maintenance window: phase-37-rehearsal-window
Pre-change backup custody: evidence/pre-change-backup-custody.md
Selected restore point: restore-point-20260425T010000Z
Restore target: disposable-customer-like-recovery-target
Restore validation: evidence/restore-validation.md
Same-day rollback decision: rollback-not-needed-after-validation
Rollback evidence: evidence/rollback-decision.md
Upgrade evidence: evidence/upgrade-window.md
Post-upgrade smoke: evidence/smoke/manifest.md
Reviewed record-chain evidence: evidence/reviewed-record-chain.txt
Clean-state validation: evidence/clean-state.md
Evidence handoff: evidence/handoff-index.md
Next review: next-business-day-health-review
EOF
}

commit_fixture() {
  local target="$1"

  git -C "${target}" add .
  git -C "${target}" commit --allow-empty -q -m "fixture"
}

assert_passes() {
  local target="$1"
  local manifest="$2"

  if ! bash "${verifier}" "${target}" --manifest "${manifest}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local manifest="$2"
  local expected="$3"

  if bash "${verifier}" "${target}" --manifest "${manifest}" >"${fail_stdout}" 2>"${fail_stderr}"; then
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
write_valid_doc "${valid_repo}"
write_valid_manifest "${valid_repo}/manifest.md"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}" "${valid_repo}/manifest.md"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
write_shared_docs "${missing_doc_repo}"
write_valid_manifest "${missing_doc_repo}/manifest.md"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "${missing_doc_repo}/manifest.md" "Missing Phase 37 restore rollback upgrade evidence rehearsal document:"

missing_backup_manifest_repo="${workdir}/missing-backup-manifest"
create_repo "${missing_backup_manifest_repo}"
write_shared_docs "${missing_backup_manifest_repo}"
write_valid_doc "${missing_backup_manifest_repo}"
write_valid_manifest "${missing_backup_manifest_repo}/manifest.md"
perl -0pi -e 's/^Pre-change backup custody:.*\n//m' "${missing_backup_manifest_repo}/manifest.md"
commit_fixture "${missing_backup_manifest_repo}"
assert_fails_with "${missing_backup_manifest_repo}" "${missing_backup_manifest_repo}/manifest.md" "Missing Phase 37 release-gate evidence manifest statement: Pre-change backup custody:"

missing_rollback_manifest_repo="${workdir}/missing-rollback-manifest"
create_repo "${missing_rollback_manifest_repo}"
write_shared_docs "${missing_rollback_manifest_repo}"
write_valid_doc "${missing_rollback_manifest_repo}"
write_valid_manifest "${missing_rollback_manifest_repo}/manifest.md"
perl -0pi -e 's/^Same-day rollback decision:.*\n//m' "${missing_rollback_manifest_repo}/manifest.md"
commit_fixture "${missing_rollback_manifest_repo}"
assert_fails_with "${missing_rollback_manifest_repo}" "${missing_rollback_manifest_repo}/manifest.md" "Missing Phase 37 release-gate evidence manifest statement: Same-day rollback decision:"

placeholder_manifest_repo="${workdir}/placeholder-manifest"
create_repo "${placeholder_manifest_repo}"
write_shared_docs "${placeholder_manifest_repo}"
write_valid_doc "${placeholder_manifest_repo}"
write_valid_manifest "${placeholder_manifest_repo}/manifest.md"
printf '\nOperator note: TODO wire trusted scope.\n' >> "${placeholder_manifest_repo}/manifest.md"
commit_fixture "${placeholder_manifest_repo}"
assert_fails_with "${placeholder_manifest_repo}" "${placeholder_manifest_repo}/manifest.md" "Placeholder or untrusted manifest value detected:"

absolute_path_manifest_repo="${workdir}/absolute-path-manifest"
create_repo "${absolute_path_manifest_repo}"
write_shared_docs "${absolute_path_manifest_repo}"
write_valid_doc "${absolute_path_manifest_repo}"
write_valid_manifest "${absolute_path_manifest_repo}/manifest.md"
printf '\nLocal output: /Users/example/evidence/manifest.md\n' >> "${absolute_path_manifest_repo}/manifest.md"
commit_fixture "${absolute_path_manifest_repo}"
assert_fails_with "${absolute_path_manifest_repo}" "${absolute_path_manifest_repo}/manifest.md" "Forbidden Phase 37 release-gate evidence manifest: workstation-local absolute path detected"

echo "verify-phase-37-restore-rollback-upgrade-evidence tests passed"
