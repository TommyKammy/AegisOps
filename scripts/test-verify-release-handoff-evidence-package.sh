#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-release-handoff-evidence-package.sh"

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

Before launch, upgrade, rollback, restore, or operator handoff closes, assemble the Phase 38 release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` and verify its manifest with `scripts/verify-release-handoff-evidence-package.sh --manifest <release-handoff-manifest.md>`.
EOF

  cat <<'EOF' > "${target}/docs/deployment/single-customer-release-bundle-inventory.md"
# Single-Customer Release Bundle Inventory

The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` is the Phase 38 handoff index that ties the release bundle identifier, install preflight result, runtime smoke, restore, rollback, upgrade, known limitations, rollback instructions, handoff owner, and next health review to one bounded record.
EOF

  cat <<'EOF' > "${target}/docs/deployment/runtime-smoke-bundle.md"
# Phase 33 Runtime Smoke Bundle

The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` must retain the runtime smoke manifest reference for launch, upgrade, rollback, restore restart, and operator handoff readiness.
EOF

  cat <<'EOF' > "${target}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
# Phase 37 Restore Rollback Upgrade Evidence Rehearsal

The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` consumes the verified restore, rollback, and upgrade release-gate manifest as the authoritative recovery evidence reference for the handoff window.
EOF

  cat <<'EOF' > "${target}/docs/deployment/operational-evidence-handoff-pack.md"
# Phase 33 Operational Evidence Retention and Audit Handoff Pack

For Phase 38 release handoff, use `docs/deployment/release-handoff-evidence-package.md` as the one launch or upgrade handoff index; this operational pack remains retained evidence guidance and does not become workflow authority.
EOF

  cat <<'EOF' > "${target}/docs/deployment/customer-like-rehearsal-environment.md"
# Customer-Like Rehearsal Environment

The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` records the install preflight and customer-like rehearsal result before launch handoff can close.
EOF

  cat <<'EOF' > "${target}/scripts/verify-single-customer-install-preflight.sh"
#!/usr/bin/env bash
exit 0
EOF

  cat <<'EOF' > "${target}/scripts/run-phase-37-runtime-smoke-gate.sh"
#!/usr/bin/env bash
exit 0
EOF

  cat <<'EOF' > "${target}/scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh"
#!/usr/bin/env bash
exit 0
EOF

  chmod +x \
    "${target}/scripts/verify-single-customer-install-preflight.sh" \
    "${target}/scripts/run-phase-37-runtime-smoke-gate.sh" \
    "${target}/scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh"
}

write_valid_package_doc() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/release-handoff-evidence-package.md"
# Phase 38 Release Handoff Evidence Package

## 1. Purpose and Boundary

This document defines the Phase 38 release handoff evidence package for a single-customer launch or reviewed upgrade.

The package is a bounded repo-owned handoff index, not a new external archive platform, compliance framework, or workflow authority.

AegisOps approval, evidence, execution, reconciliation, readiness, and recovery truth remains in the reviewed AegisOps records and release-gate evidence; downstream tickets, substrate receipts, and operator notes are subordinate context only.

## 2. Required Handoff Entries

Every release handoff manifest must include release readiness summary, release bundle identifier, install preflight result, runtime smoke result, backup, restore, rollback, and upgrade rehearsal reference, known limitations, rollback instructions, handoff owner, and next health review.

Release notes and known limitations must point to the operator handoff record and the rollback decision record so a launch reviewer can see whether limitations block launch, normal operation, or rollback acceptance.

## 3. Evidence Sources

Install preflight evidence comes from `scripts/verify-single-customer-install-preflight.sh --env-file <runtime-env-file>`.

Runtime smoke evidence comes from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`.

Restore, rollback, and upgrade evidence comes from `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>`.

## 4. Blocking Outcomes

A failed install preflight, runtime smoke, restore validation, rollback rehearsal, upgrade evidence check, or missing known-limitation review blocks launch handoff and normal operation until the failed prerequisite is fixed or the refusal is retained as the handoff outcome.

## 5. Retention and Path Hygiene

The package keeps the current launch or upgrade handoff, the linked release-gate manifest, the latest runtime smoke manifest, and the next health review expectation; it does not promise unlimited retention.

The manifest must use repo-relative paths, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, and `<release-handoff-manifest.md>`.

## 6. Verification

Verify a retained release handoff manifest with `scripts/verify-release-handoff-evidence-package.sh --manifest <release-handoff-manifest.md>`.

The verifier fails closed when required handoff entries are missing, placeholder-only, sample, guessed, stale, workstation-local, or when required cross-links to Phase 37 smoke, restore, rollback, upgrade, release bundle, runbook, and operational handoff material are missing.

## 7. Out of Scope

External archive platforms, unlimited retention promises, compliance-framework generalization, external ticket lifecycle authority, multi-customer evidence warehouses, direct backend exposure, optional-extension launch gates, and customer-private production access are out of scope.
EOF

  cat <<'EOF' > "${target}/docs/deployment/release-handoff-evidence-manifest.template.md"
# Phase 38 Release Handoff Evidence Manifest

Release readiness summary: <replace-with-reviewed-readiness-summary>
Release bundle identifier: aegisops-single-customer-<repository-revision>
Install preflight result: <replace-with-install-preflight-result-reference>
Runtime smoke result: <replace-with-runtime-smoke-manifest-reference>
Backup restore rollback upgrade rehearsal: <replace-with-release-gate-manifest-reference>
Known limitations: <replace-with-reviewed-known-limitations-reference>
Rollback instructions: <replace-with-reviewed-rollback-instructions-reference>
Handoff owner: <replace-with-named-operator-or-maintainer>
Next health review: <replace-with-next-business-review-reference>
Authority boundary: AegisOps approval, evidence, execution, reconciliation, readiness, and recovery records remain authoritative; external records are subordinate context only.
EOF

  cat <<'EOF' > "${target}/docs/deployment/release-handoff-evidence-manifest.single-customer-pilot.example.md"
# Phase 38 Release Handoff Evidence Manifest - Filled Redacted Single-Customer Pilot Example

Release readiness summary: Pilot release accepted for one redacted customer environment after reviewed preflight, smoke, restore, rollback, upgrade, and known-limitations evidence all referenced the same release identifier.
Release bundle identifier: aegisops-single-customer-pilot-2026-04-27-c4527e5
Install preflight result: docs/deployment/evidence-examples/single-customer-pilot/install-preflight-result.redacted.md records PASS for the reviewed runtime env shape with secret values omitted.
Runtime smoke result: docs/deployment/evidence-examples/single-customer-pilot/runtime-smoke/manifest.md records PASS for readiness, protected read-only reachability, queue sanity, and first low-risk action preconditions.
Backup restore rollback upgrade rehearsal: docs/deployment/evidence-examples/single-customer-pilot/release-gate-manifest.md records backup custody, restore validation, rollback-not-needed decision, post-upgrade smoke, and clean-state evidence.
Known limitations: docs/deployment/evidence-examples/single-customer-pilot/known-limitations.redacted.md records accepted limitations, non-blocking follow-up owners, and rollback acceptance criteria.
Rollback instructions: docs/runbook.md#43-rollback-and-restore references the reviewed rollback path and selected restore point for this release identifier.
Handoff owner: pilot-owner-redacted, IT Operations, Information Systems Department.
Next health review: 2026-04-28 business-day health review, queue review, and backup-drift check owned by pilot-owner-redacted.
Refused or missing evidence handling: Customer-private raw log payloads and live credential screenshots were refused for the retained packet; the packet retains redacted evidence summaries and clean-state validation instead of substituting private data.
Subordinate context only: Wazuh alert references, Shuffle execution receipts, Zammad ticket links, assistant notes, ML shadow observations, downstream receipts, and optional evidence fields are retained as context only and do not own release readiness, case state, approval, execution, reconciliation, restore, rollback, or handoff truth.
Authority boundary: AegisOps approval, evidence, execution, reconciliation, readiness, and recovery records remain authoritative; external records are subordinate context only.
EOF
}

write_valid_manifest() {
  local path="$1"

  cat <<'EOF' > "${path}"
# Phase 38 Release Handoff Evidence Manifest

Release readiness summary: evidence/release-readiness-summary.md
Release bundle identifier: aegisops-single-customer-3e831fd
Install preflight result: evidence/install-preflight-result.md
Runtime smoke result: evidence/runtime-smoke/manifest.md
Backup restore rollback upgrade rehearsal: evidence/release-gate-manifest.md
Known limitations: docs/releases/phase38-known-limitations.md
Rollback instructions: docs/runbook.md#rollback
Handoff owner: single-customer-operator
Next health review: next-business-day-health-review
Authority boundary: AegisOps approval, evidence, execution, reconciliation, readiness, and recovery records remain authoritative; external records are subordinate context only.
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
write_valid_package_doc "${valid_repo}"
write_valid_manifest "${valid_repo}/manifest.md"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}" "${valid_repo}/manifest.md"

missing_exemplar_repo="${workdir}/missing-exemplar"
create_repo "${missing_exemplar_repo}"
write_shared_docs "${missing_exemplar_repo}"
write_valid_package_doc "${missing_exemplar_repo}"
write_valid_manifest "${missing_exemplar_repo}/manifest.md"
rm "${missing_exemplar_repo}/docs/deployment/release-handoff-evidence-manifest.single-customer-pilot.example.md"
commit_fixture "${missing_exemplar_repo}"
assert_fails_with "${missing_exemplar_repo}" "${missing_exemplar_repo}/manifest.md" "Missing Phase 38 filled redacted release handoff evidence exemplar:"

for missing_entry in \
  "Release readiness summary:" \
  "Runtime smoke result:" \
  "Rollback instructions:" \
  "Known limitations:" \
  "Next health review:"; do
  missing_repo="${workdir}/missing-${missing_entry//[^A-Za-z0-9]/-}"
  create_repo "${missing_repo}"
  write_shared_docs "${missing_repo}"
  write_valid_package_doc "${missing_repo}"
  write_valid_manifest "${missing_repo}/manifest.md"
  perl -0pi -e "s/^\\Q${missing_entry}\\E.*\\n//m" "${missing_repo}/manifest.md"
  commit_fixture "${missing_repo}"
  assert_fails_with "${missing_repo}" "${missing_repo}/manifest.md" "Missing Phase 38 release handoff manifest entry: ${missing_entry}"
done

missing_restore_repo="${workdir}/missing-restore-entry"
create_repo "${missing_restore_repo}"
write_shared_docs "${missing_restore_repo}"
write_valid_package_doc "${missing_restore_repo}"
write_valid_manifest "${missing_restore_repo}/manifest.md"
perl -0pi -e 's/^Backup restore rollback upgrade rehearsal:.*\n//m' "${missing_restore_repo}/manifest.md"
commit_fixture "${missing_restore_repo}"
assert_fails_with "${missing_restore_repo}" "${missing_restore_repo}/manifest.md" "Missing Phase 38 release handoff manifest entry: Backup restore rollback upgrade rehearsal:"

placeholder_repo="${workdir}/placeholder-manifest"
create_repo "${placeholder_repo}"
write_shared_docs "${placeholder_repo}"
write_valid_package_doc "${placeholder_repo}"
write_valid_manifest "${placeholder_repo}/manifest.md"
printf '\nOperator note: TODO fill known limitations.\n' >> "${placeholder_repo}/manifest.md"
commit_fixture "${placeholder_repo}"
assert_fails_with "${placeholder_repo}" "${placeholder_repo}/manifest.md" "Placeholder or untrusted Phase 38 release handoff manifest value detected:"

absolute_path_repo="${workdir}/absolute-path-manifest"
create_repo "${absolute_path_repo}"
write_shared_docs "${absolute_path_repo}"
write_valid_package_doc "${absolute_path_repo}"
write_valid_manifest "${absolute_path_repo}/manifest.md"
printf '\nLocal evidence: /%s/%s/release-handoff/manifest.md\n' "Users" "example" >> "${absolute_path_repo}/manifest.md"
commit_fixture "${absolute_path_repo}"
assert_fails_with "${absolute_path_repo}" "${absolute_path_repo}/manifest.md" "Forbidden Phase 38 release handoff evidence manifest: workstation-local absolute path detected"

missing_cross_link_repo="${workdir}/missing-cross-link"
create_repo "${missing_cross_link_repo}"
write_shared_docs "${missing_cross_link_repo}"
write_valid_package_doc "${missing_cross_link_repo}"
write_valid_manifest "${missing_cross_link_repo}/manifest.md"
printf '# Phase 33 Runtime Smoke Bundle\n' > "${missing_cross_link_repo}/docs/deployment/runtime-smoke-bundle.md"
commit_fixture "${missing_cross_link_repo}"
assert_fails_with "${missing_cross_link_repo}" "${missing_cross_link_repo}/manifest.md" "Missing runtime smoke release handoff package link:"

echo "verify-release-handoff-evidence-package tests passed"
