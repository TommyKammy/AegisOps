#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-pilot-readiness-checklist.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment" "${target}/docs"
}

write_valid_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/pilot-readiness-checklist.md"
# Single-Customer Pilot Readiness Checklist and Entry Criteria

## 1. Purpose and Boundary

This document defines the reviewed entry checklist for starting one single-customer pilot.

The entry decision is a reviewed go, no-go, or go-with-explicit-limitations decision for one customer environment; it is not a compliance certification, multi-customer rollout approval, SLA commitment, or 24x7 support promise.

## 2. Entry Decision Summary

The pilot may start only when release readiness, runtime smoke, detector activation scope, coordination pilot scope, assistant limitations, data retention, and evidence handoff are reviewed together for the same release identifier.

## 3. Readiness Checklist

Release readiness must be bound to `docs/deployment/single-customer-release-bundle-inventory.md` and `docs/deployment/release-handoff-evidence-package.md` for the same `aegisops-single-customer-<repository-revision>` release identifier.

Runtime smoke must pass through `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` and retain the smoke `manifest.md` as entry evidence.

Detector activation scope must follow `docs/detector-activation-evidence-handoff.md` and name only the reviewed candidate rules, fixture evidence, activation owner, disable owner, rollback owner, expected alert volume, false-positive review, and next-review date accepted for the pilot.

For the filled single-customer packet shape, pilot owners must compare retained detector activation evidence against the provided single-customer example before accepting detector scope into the entry decision.

The provided single-customer example is `docs/deployment/detector-activation-evidence.single-customer-pilot.example.md`.

Coordination scope must follow `docs/operations-zammad-live-pilot-boundary.md`; Zammad remains link-first, coordination-only, and non-authoritative for AegisOps case, action, approval, execution, and reconciliation records.

Zammad coordination rehearsal evidence must include the checked available, degraded, and unavailable scenarios from `control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json` so stale reads, mismatched ticket identifiers, and missing or placeholder credentials remain visible without becoming AegisOps truth.

Assistant output remains advisory-only and non-authoritative; it must stay grounded in reviewed control-plane records and linked evidence and must not approve, execute, reconcile, close, or widen pilot scope.

## 4. Required Entry Evidence

Evidence handoff must name the release handoff record, runtime smoke manifest, detector activation handoff, coordination pilot status, assistant limitation statement, known-limitations review, handoff owner, and next health review.

## 5. Known Limitations, Retention, and Evidence Handoff

Known limitations must be explicit, reviewed, and tied to the entry decision, including whether each limitation blocks pilot start, allows pilot start with a follow-up owner, or requires rollback or disable evidence.

Pilot owners must record the known-limitation and retention decision in `docs/deployment/known-limitations-retention-decision-template.md` before the entry decision is treated as reviewed.

Data retention for the pilot is bounded to the current release handoff, runtime smoke manifest, detector activation evidence handoff, Zammad coordination reference, assistant limitation note, and next health review expectation; it is not an unlimited archive.

## 6. Blocking Outcomes

Missing release readiness, failed runtime smoke, missing detector activation owner, missing disable or rollback owner, missing Zammad credential custody, missing assistant limitation statement, missing known-limitations review, missing evidence handoff owner, or mixed release identifiers blocks pilot entry.

## 7. Verification

Verify this checklist with `scripts/verify-pilot-readiness-checklist.sh`.

Negative validation for the verifier is `scripts/test-verify-pilot-readiness-checklist.sh`.

## 8. Out of Scope

Formal compliance certification, multi-customer rollout, SLA or 24x7 support promise, external archive platform design, customer-private production access, optional-extension launch gates, direct backend exposure, ticket-system authority, and assistant-owned workflow authority are out of scope.
EOF

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook

Before starting a single-customer pilot, review `docs/deployment/pilot-readiness-checklist.md` and verify it with `scripts/verify-pilot-readiness-checklist.sh` so release readiness, runtime smoke, detector activation scope, Zammad coordination scope, assistant limitations, data retention, known limitations, and evidence handoff are decided together.
EOF

  cat <<'EOF' > "${target}/docs/deployment/single-customer-release-bundle-inventory.md"
# Single-Customer Release Bundle Inventory

Pilot entry must use `docs/deployment/pilot-readiness-checklist.md` after the single-customer release bundle inventory is bound to the same `aegisops-single-customer-<repository-revision>` release identifier.
EOF

  cat <<'EOF' > "${target}/docs/deployment/release-handoff-evidence-package.md"
# Phase 38 Release Handoff Evidence Package

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this release handoff package as the reviewed release-readiness and known-limitations evidence source for the pilot entry decision.

For pilot launch review, record the known-limitation and retention decision with `docs/deployment/known-limitations-retention-decision-template.md` so `accepted-with-owner`, blocking, rollback, disable, follow-up, and not-reviewed states, plus owners, operator-visible behavior, revisit dates, and bounded retention decisions, are reviewed in one place.
EOF

  cat <<'EOF' > "${target}/docs/deployment/runtime-smoke-bundle.md"
# Phase 33 Runtime Smoke Bundle

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` treats the retained runtime smoke `manifest.md` from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` as required entry evidence.
EOF

  cat <<'EOF' > "${target}/docs/detector-activation-evidence-handoff.md"
# Detector Activation Evidence Handoff Manifest

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this detector activation evidence handoff as the bounded detector scope, owner, rollback, disable, expected-volume, false-positive, and known-limitation evidence for pilot entry.
EOF

  cat <<'EOF' > "${target}/docs/deployment/detector-activation-evidence.single-customer-pilot.example.md"
# Detector Activation Evidence Handoff - Filled Redacted Single-Customer Pilot Example

Authority boundary: Wazuh rule state remains substrate evidence; AegisOps-owned alert, case, evidence, reconciliation, and release-gate records remain workflow truth.
EOF

  cat <<'EOF' > "${target}/docs/operations-zammad-live-pilot-boundary.md"
# Operations Zammad-First Live Pilot Boundary and Credential Custody

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this Zammad-first boundary as the coordination pilot scope and credential-custody prerequisite for pilot entry.
EOF

  cat <<'EOF' > "${target}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
# Phase 15 Identity-Grounded Analyst Assistant Boundary

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` must keep this assistant boundary advisory-only and non-authoritative for pilot entry.
EOF

  cat <<'EOF' > "${target}/docs/deployment/operational-evidence-handoff-pack.md"
# Phase 33 Operational Evidence Retention and Audit Handoff Pack

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` is the reviewed entry decision surface that points operators to the retained release, smoke, detector, coordination, limitation, and evidence handoff records before pilot start.
EOF

  cat <<'EOF' > "${target}/docs/deployment/known-limitations-retention-decision-template.md"
# Known Limitations and Retention Decision Template

This template is the reviewed decision record for a bounded single-customer pilot go/no-go review.

A completed template must distinguish no known blocking limitation from not reviewed.

Disposition values: blocking, accepted-with-owner, rollback, disable, follow-up, not-reviewed.

Every accepted-with-owner limitation must name the owner, expected operator-visible behavior, revisit date, affected surface, and retention decision.

Retention decisions must be bounded to reviewed pilot evidence, not unlimited raw-log retention.

Do not include secrets, live credentials, customer-private raw logs, raw forwarded-header values, unsigned identity hints, workstation-local paths, or customer-private ticket content.

Subordinate systems, optional extensions, external tickets, detector substrates, assistant output, and bounded logs are context only; they do not own AegisOps approval, execution, reconciliation, readiness, release, or pilot-entry truth.

Unsupported compliance certification, SLA commitments, 24x7 support promises, public launch approval, multi-customer rollout, multi-tenant expansion, legal hold automation, and runtime retention enforcement are out of scope.
EOF

  mkdir -p "${target}/scripts"
  touch "${target}/scripts/test-verify-pilot-readiness-checklist.sh"
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
write_valid_docs "${valid_repo}"
assert_passes "${valid_repo}"

missing_checklist_repo="${workdir}/missing-checklist"
create_repo "${missing_checklist_repo}"
write_valid_docs "${missing_checklist_repo}"
rm "${missing_checklist_repo}/docs/deployment/pilot-readiness-checklist.md"
assert_fails_with "${missing_checklist_repo}" "Missing pilot readiness checklist:"

missing_smoke_repo="${workdir}/missing-smoke"
create_repo "${missing_smoke_repo}"
write_valid_docs "${missing_smoke_repo}"
perl -0pi -e 's/^Runtime smoke must pass.*\n//m' "${missing_smoke_repo}/docs/deployment/pilot-readiness-checklist.md"
assert_fails_with "${missing_smoke_repo}" 'Missing pilot readiness checklist statement: Runtime smoke must pass through `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`'

missing_detector_example_repo="${workdir}/missing-detector-example"
create_repo "${missing_detector_example_repo}"
write_valid_docs "${missing_detector_example_repo}"
perl -0pi -e 's/^For the filled single-customer packet shape.*\n\n^The provided single-customer example.*\n//m' "${missing_detector_example_repo}/docs/deployment/pilot-readiness-checklist.md"
assert_fails_with "${missing_detector_example_repo}" "Missing pilot readiness checklist statement: For the filled single-customer packet shape, pilot owners must compare retained detector activation evidence against the provided single-customer example before accepting detector scope into the entry decision."

missing_detector_exemplar_file_repo="${workdir}/missing-detector-exemplar-file"
create_repo "${missing_detector_exemplar_file_repo}"
write_valid_docs "${missing_detector_exemplar_file_repo}"
rm "${missing_detector_exemplar_file_repo}/docs/deployment/detector-activation-evidence.single-customer-pilot.example.md"
assert_fails_with "${missing_detector_exemplar_file_repo}" "Missing filled redacted detector activation evidence exemplar:"

missing_known_limitations_template_repo="${workdir}/missing-known-limitations-template"
create_repo "${missing_known_limitations_template_repo}"
write_valid_docs "${missing_known_limitations_template_repo}"
rm "${missing_known_limitations_template_repo}/docs/deployment/known-limitations-retention-decision-template.md"
assert_fails_with "${missing_known_limitations_template_repo}" "Missing known limitations and retention decision template:"

missing_known_limitations_template_link_repo="${workdir}/missing-known-limitations-template-link"
create_repo "${missing_known_limitations_template_link_repo}"
write_valid_docs "${missing_known_limitations_template_link_repo}"
perl -0pi -e 's/^Pilot owners must record the known-limitation.*\n//m' "${missing_known_limitations_template_link_repo}/docs/deployment/pilot-readiness-checklist.md"
assert_fails_with "${missing_known_limitations_template_link_repo}" 'Missing pilot readiness checklist statement: Pilot owners must record the known-limitation and retention decision in `docs/deployment/known-limitations-retention-decision-template.md`'

missing_release_handoff_template_link_repo="${workdir}/missing-release-handoff-template-link"
create_repo "${missing_release_handoff_template_link_repo}"
write_valid_docs "${missing_release_handoff_template_link_repo}"
perl -0pi -e 's/^For pilot launch review, record the known-limitation.*\n//m' "${missing_release_handoff_template_link_repo}/docs/deployment/release-handoff-evidence-package.md"
assert_fails_with "${missing_release_handoff_template_link_repo}" 'Missing release handoff known-limitation template link: For pilot launch review, record the known-limitation and retention decision with `docs/deployment/known-limitations-retention-decision-template.md`'

missing_disposition_values_repo="${workdir}/missing-disposition-values"
create_repo "${missing_disposition_values_repo}"
write_valid_docs "${missing_disposition_values_repo}"
perl -0pi -e 's/^Disposition values: blocking, accepted-with-owner, rollback, disable, follow-up, not-reviewed\.\n//m' "${missing_disposition_values_repo}/docs/deployment/known-limitations-retention-decision-template.md"
assert_fails_with "${missing_disposition_values_repo}" "Missing known limitations retention template statement: Disposition values: blocking, accepted-with-owner, rollback, disable, follow-up, not-reviewed."

missing_accepted_limitation_owner_repo="${workdir}/missing-accepted-limitation-owner"
create_repo "${missing_accepted_limitation_owner_repo}"
write_valid_docs "${missing_accepted_limitation_owner_repo}"
perl -0pi -e 's/^Every accepted-with-owner limitation must.*\n//m' "${missing_accepted_limitation_owner_repo}/docs/deployment/known-limitations-retention-decision-template.md"
assert_fails_with "${missing_accepted_limitation_owner_repo}" "Missing known limitations retention template statement: Every accepted-with-owner limitation must name the owner, expected operator-visible behavior, revisit date, affected surface, and retention decision."

missing_bounded_retention_repo="${workdir}/missing-bounded-retention"
create_repo "${missing_bounded_retention_repo}"
write_valid_docs "${missing_bounded_retention_repo}"
perl -0pi -e 's/^Retention decisions must be bounded.*\n//m' "${missing_bounded_retention_repo}/docs/deployment/known-limitations-retention-decision-template.md"
assert_fails_with "${missing_bounded_retention_repo}" "Missing known limitations retention template statement: Retention decisions must be bounded to reviewed pilot evidence, not unlimited raw-log retention."

missing_coordination_link_repo="${workdir}/missing-coordination-link"
create_repo "${missing_coordination_link_repo}"
write_valid_docs "${missing_coordination_link_repo}"
printf '# Operations Zammad-First Live Pilot Boundary and Credential Custody\n' > "${missing_coordination_link_repo}/docs/operations-zammad-live-pilot-boundary.md"
assert_fails_with "${missing_coordination_link_repo}" 'Missing coordination pilot readiness link: The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this Zammad-first boundary'

missing_coordination_rehearsal_repo="${workdir}/missing-coordination-rehearsal"
create_repo "${missing_coordination_rehearsal_repo}"
write_valid_docs "${missing_coordination_rehearsal_repo}"
perl -0pi -e 's/^Zammad coordination rehearsal evidence must.*\n//m' "${missing_coordination_rehearsal_repo}/docs/deployment/pilot-readiness-checklist.md"
assert_fails_with "${missing_coordination_rehearsal_repo}" 'Missing pilot readiness checklist statement: Zammad coordination rehearsal evidence must include the checked available, degraded, and unavailable scenarios from `control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json`'

forbidden_authority_repo="${workdir}/forbidden-authority"
create_repo "${forbidden_authority_repo}"
write_valid_docs "${forbidden_authority_repo}"
printf '\nThe assistant may approve pilot exceptions.\n' >> "${forbidden_authority_repo}/docs/deployment/pilot-readiness-checklist.md"
assert_fails_with "${forbidden_authority_repo}" "Forbidden pilot readiness checklist statement: assistant may approve"

absolute_path_repo="${workdir}/absolute-path"
create_repo "${absolute_path_repo}"
write_valid_docs "${absolute_path_repo}"
printf '\nLocal evidence: /%s/%s/pilot-readiness.md\n' "Users" "example" >> "${absolute_path_repo}/docs/deployment/pilot-readiness-checklist.md"
assert_fails_with "${absolute_path_repo}" "Forbidden pilot readiness guidance: workstation-local absolute path detected"

echo "Pilot readiness checklist verifier tests passed."
