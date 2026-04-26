#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-support-playbook-break-glass-rehearsal.sh"

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

write_shared_files() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/runbook.md"
# AegisOps Runbook

For pilot support degradation, break-glass rehearsal, and operator-readable evidence expectations, use `docs/deployment/support-playbook-break-glass-rehearsal.md` and verify it with `scripts/verify-support-playbook-break-glass-rehearsal.sh`.
EOF

  cat <<'EOF' > "${target}/docs/deployment/pilot-readiness-checklist.md"
# Single-Customer Pilot Readiness Checklist and Entry Criteria

The support playbook in `docs/deployment/support-playbook-break-glass-rehearsal.md` is the reviewed pilot degradation and break-glass rehearsal reference; pilot entry remains blocked if support expectations would require 24x7 coverage, customer-specific support terms, or emergency authority bypass.
EOF

  cat <<'EOF' > "${target}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
# Phase 37 Restore Rollback Upgrade Evidence Rehearsal

Support escalation from `docs/deployment/support-playbook-break-glass-rehearsal.md` must route rollback and restore decisions back to this release-gate rehearsal and retain refusal reason plus clean-state evidence for failed paths.
EOF

  cat <<'EOF' > "${target}/docs/deployment/operational-evidence-handoff-pack.md"
# Phase 33 Operational Evidence Retention and Audit Handoff Pack

Support playbook evidence from `docs/deployment/support-playbook-break-glass-rehearsal.md` may be retained in this handoff pack only as operator-readable evidence attached to reviewed AegisOps records.
EOF

  touch "${target}/scripts/test-verify-support-playbook-break-glass-rehearsal.sh"
}

write_valid_playbook() {
  local target="$1"

  cat <<'EOF' > "${target}/docs/deployment/support-playbook-break-glass-rehearsal.md"
# Support Playbook and Break-Glass Rehearsal

## 1. Purpose and Boundary

This playbook tells maintainers and operators what to inspect when the single-customer pilot degrades without creating emergency authority bypass.

The reviewed operating posture remains business-hours, operator-led, and subordinate to AegisOps authoritative records.

The playbook covers source, detector, coordination, assistant, runtime, rollback, and restore degradation for the reviewed single-customer pilot.

It does not create 24x7 on-call coverage, a customer-specific support contract, direct backend access, direct substrate authority, or emergency authority bypass.

## 2. Common Pilot Failure Modes

| Failure mode | Inspect first | Do not infer |
| --- | --- | --- |
| Source degradation | Source-family evidence, ingest custody, replay or fixture proof, source timestamp, and AegisOps linkage. | Tenant, customer, alert, case, or evidence linkage from names or path shape. |
| Detector degradation | Detector activation handoff, candidate rule identifier, fixture evidence, expected volume, false-positive review, disable owner, rollback owner, and next review. | Detector output as case, approval, execution, or rollback truth. |
| Coordination degradation | Zammad boundary, endpoint, reviewed token source, reachability, and explicit AegisOps linkage. | Ticket state, comments, assignee, or closure as AegisOps authority. |
| Assistant degradation | Assistant citations, reviewed record ids, linked evidence ids, uncertainty flags, and limited surfaces. | Advisory text as approval, execution, reconciliation, or closure. |
| Runtime degradation | Reverse-proxy health, readiness, runtime inspection, compose state, bounded logs, env contract, and migration bootstrap. | Direct backend health, optional-extension health, or partial container state as readiness. |
| Rollback degradation | Rollback decision owner, selected restore point, backup custody, revisions, smoke result, and clean-state proof. | A clean retry summary as proof that the failed path disappeared. |
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

## 7. Verification

Verify this playbook with `scripts/verify-support-playbook-break-glass-rehearsal.sh`.

Negative validation for the verifier is `scripts/test-verify-support-playbook-break-glass-rehearsal.sh`.

## 8. Out of Scope

Formal SLA support, 24x7 support coverage, direct customer-private production access, customer-specific paid support terms, emergency authority bypass, direct backend exposure, direct substrate authority, ticket-system authority, detector-owned workflow truth, assistant-owned workflow truth, and optional-extension launch gates are out of scope.
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

forbidden_phrase_case_index=0

assert_rejects_forbidden_playbook_phrase() {
  local phrase="$1"
  local target

  forbidden_phrase_case_index=$((forbidden_phrase_case_index + 1))
  target="${workdir}/forbidden-playbook-phrase-${forbidden_phrase_case_index}"

  create_repo "${target}"
  write_shared_files "${target}"
  write_valid_playbook "${target}"
  {
    printf '\n'
    printf '%s.\n' "${phrase}"
  } >> "${target}/docs/deployment/support-playbook-break-glass-rehearsal.md"
  commit_fixture "${target}"
  assert_fails_with "${target}" "Forbidden support playbook statement: ${phrase}"
}

workstation_path_case_index=0

assert_rejects_workstation_path() {
  local path_fragment="$1"
  local target

  workstation_path_case_index=$((workstation_path_case_index + 1))
  target="${workdir}/workstation-path-${workstation_path_case_index}"

  create_repo "${target}"
  write_shared_files "${target}"
  write_valid_playbook "${target}"
  {
    printf '\n'
    printf 'Use %s for local evidence.\n' "${path_fragment}"
  } >> "${target}/docs/deployment/support-playbook-break-glass-rehearsal.md"

  commit_fixture "${target}"
  assert_fails_with "${target}" "Forbidden support playbook guidance: workstation-local absolute path detected"
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_shared_files "${valid_repo}"
write_valid_playbook "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_playbook_repo="${workdir}/missing-playbook"
create_repo "${missing_playbook_repo}"
write_shared_files "${missing_playbook_repo}"
commit_fixture "${missing_playbook_repo}"
assert_fails_with "${missing_playbook_repo}" "Missing support playbook and break-glass rehearsal:"

missing_detector_repo="${workdir}/missing-detector"
create_repo "${missing_detector_repo}"
write_shared_files "${missing_detector_repo}"
write_valid_playbook "${missing_detector_repo}"
perl -0pi -e 's/^Detector handling: .*?\n\n//m' "${missing_detector_repo}/docs/deployment/support-playbook-break-glass-rehearsal.md"
commit_fixture "${missing_detector_repo}"
assert_fails_with "${missing_detector_repo}" "Missing support playbook statement: Detector handling:"

missing_break_glass_repo="${workdir}/missing-break-glass"
create_repo "${missing_break_glass_repo}"
write_shared_files "${missing_break_glass_repo}"
write_valid_playbook "${missing_break_glass_repo}"
perl -0pi -e 's/^Break-glass custody is .*?\n\n//m' "${missing_break_glass_repo}/docs/deployment/support-playbook-break-glass-rehearsal.md"
commit_fixture "${missing_break_glass_repo}"
assert_fails_with "${missing_break_glass_repo}" "Missing support playbook statement: Break-glass custody is"

missing_restore_link_repo="${workdir}/missing-restore-link"
create_repo "${missing_restore_link_repo}"
write_shared_files "${missing_restore_link_repo}"
write_valid_playbook "${missing_restore_link_repo}"
printf '# Phase 37 Restore Rollback Upgrade Evidence Rehearsal\n' > "${missing_restore_link_repo}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
commit_fixture "${missing_restore_link_repo}"
assert_fails_with "${missing_restore_link_repo}" "Missing restore rehearsal support playbook link:"

for forbidden_phrase in \
  "24x7 on-call is provided" \
  "SLA support is provided" \
  "customer-specific support contract is provided" \
  "emergency authority bypass is approved" \
  "break-glass may approve" \
  "break-glass may execute" \
  "break-glass may reconcile" \
  "break-glass may close" \
  "break-glass may close tickets" \
  "break-glass may activate detectors" \
  "break-glass may deactivate detectors" \
  "break-glass may enable detectors" \
  "break-glass may mark tickets authoritative" \
  "break-glass may mark ticket state authoritative" \
  "break-glass may change rollback acceptance" \
  "break-glass may approve rollback acceptance" \
  "break-glass may override rollback acceptance" \
  "ticket state is authoritative" \
  "tickets are authoritative" \
  "mark ticket state authoritative" \
  "detector output is authoritative" \
  "detector activation is approved by break-glass" \
  "assistant output is authoritative" \
  "rollback acceptance is approved" \
  "rollback acceptance is authoritative" \
  "direct backend access is approved" \
  "personal session credential is acceptable" \
  "placeholder credential is acceptable"; do
  assert_rejects_forbidden_playbook_phrase "${forbidden_phrase}"
done

assert_rejects_workstation_path "$(printf '~%sexample%sprivate%ssupport-note.md' '/' '/' '/')"
assert_rejects_workstation_path "$(printf '%shome%sexample%sprivate%ssupport-note.md' '/' '/' '/' '/')"
assert_rejects_workstation_path "$(printf '%sUsers/example/private/support-note.md' '/')"
assert_rejects_workstation_path "$(printf 'C:%sUsers%sexample%sprivate%ssupport-note.md' '/' '/' '/' '/')"
assert_rejects_workstation_path "$(printf 'C:%sUSERS%sexample%sprivate%ssupport-note.md' '/' '/' '/' '/')"
assert_rejects_workstation_path "$(printf 'C:%bUsers%bexample%bprivate%bsupport-note.md' '\\' '\\' '\\' '\\')"

echo "Support playbook and break-glass rehearsal verifier tests passed."
