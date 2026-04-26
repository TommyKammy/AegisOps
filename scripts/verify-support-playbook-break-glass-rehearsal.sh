#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
playbook_path="${repo_root}/docs/deployment/support-playbook-break-glass-rehearsal.md"
runbook_path="${repo_root}/docs/runbook.md"
pilot_readiness_path="${repo_root}/docs/deployment/pilot-readiness-checklist.md"
restore_path="${repo_root}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
verifier_test_path="${repo_root}/scripts/test-verify-support-playbook-break-glass-rehearsal.sh"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

reject_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if grep -Fqi -- "${phrase}" "${path}"; then
    echo "Forbidden ${description}: ${phrase}" >&2
    exit 1
  fi
}

reject_workstation_paths() {
  local description="$1"
  shift

  local macos_home_pattern linux_home_pattern windows_home_pattern workstation_local_path_pattern
  macos_home_pattern='/'"Users"'/[^[:space:])>]+'
  linux_home_pattern='/'"home"'/[^[:space:])>]+'
  windows_home_pattern='[A-Za-z]:[\\/][Uu][Ss][Ee][Rr][Ss][\\/][^[:space:])>]+'
  workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"

  if grep -Eq "${workstation_local_path_pattern}" "$@"; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi
}

require_file "${playbook_path}" "support playbook and break-glass rehearsal"
require_file "${runbook_path}" "runbook"
require_file "${pilot_readiness_path}" "pilot readiness checklist"
require_file "${restore_path}" "restore rollback upgrade evidence rehearsal"
require_file "${handoff_path}" "operational evidence handoff pack"
require_file "${verifier_test_path}" "support playbook verifier tests"

required_headings=(
  "# Support Playbook and Break-Glass Rehearsal"
  "## 1. Purpose and Boundary"
  "## 2. Common Pilot Failure Modes"
  "## 3. Degraded Path Handling"
  "## 4. Break-Glass Custody and Rehearsal"
  "## 5. Rollback and Restore Escalation"
  "## 6. Evidence Collection Expectations"
  "## 7. Verification"
  "## 8. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${playbook_path}" "${heading}" "support playbook heading"
done

required_playbook_phrases=(
  "This playbook tells maintainers and operators what to inspect when the single-customer pilot degrades without creating emergency authority bypass."
  "The reviewed operating posture remains business-hours, operator-led, and subordinate to AegisOps authoritative records."
  "The playbook covers source, detector, coordination, assistant, runtime, rollback, and restore degradation for the reviewed single-customer pilot."
  "It does not create 24x7 on-call coverage, a customer-specific support contract, direct backend access, direct substrate authority, or emergency authority bypass."
  "| Source degradation |"
  "| Detector degradation |"
  "| Coordination degradation |"
  "| Assistant degradation |"
  "| Runtime degradation |"
  "| Approval handling degradation |"
  "| Rollback degradation |"
  "| Restore degradation |"
  "Source handling: inspect the reviewed source-family evidence, ingest custody, replay or fixture proof, source timestamp, and explicit linkage to the AegisOps alert, case, or evidence record before widening source scope."
  "Detector handling: inspect the detector activation evidence handoff, candidate rule identifier, fixture and parser evidence, expected volume, false-positive review, disable owner, rollback owner, and next-review date before trusting detector output."
  'Coordination handling: inspect `docs/operations-zammad-live-pilot-boundary.md`, `AEGISOPS_ZAMMAD_BASE_URL`, the reviewed token source reference, endpoint reachability, and explicit AegisOps linkage before treating a ticket pointer as usable coordination context.'
  "Assistant handling: inspect the assistant boundary, citations, reviewed record ids, linked evidence ids, uncertainty flags, and disabled or limited assistant surfaces before relying on an advisory summary."
  "Runtime handling: inspect the reverse-proxy health, readiness, runtime inspection, compose status, bounded logs, runtime env contract, and migration bootstrap evidence before admitting normal operator use."
  'Approval handling: inspect `docs/runbook.md`, the AegisOps action request, approval decision record, approver or fallback approver name, denial or timeout reason, unchanged action scope, directly linked evidence, and any break-glass closeout proof before treating approval handling as complete or escalation-ready.'
  "Rollback handling: inspect the same-day rollback decision owner, selected restore point, pre-change backup custody, before-and-after repository revision, smoke result, and clean-state evidence before closing the maintenance window."
  "Restore handling: inspect backup provenance, selected restore point, empty restore target expectation, post-restore readiness, record-chain validation, and clean-state proof before returning to service."
  "Break-glass custody is a documented recovery exception, not an alternate approval path, permanent operator shortcut, or way to bypass reviewed AegisOps authority."
  "A break-glass rehearsal must name the trigger, primary custodian, backup custodian, approving reviewer, bounded access window, affected runtime binding, redacted evidence location, rotation follow-up owner, and return-to-normal confirmation."
  "Missing, placeholder, sample, TODO, unsigned, browser-state, raw forwarded-header, or personal-session credentials keep break-glass blocked until the reviewed custody source is repaired."
  "Break-glass use must not approve, execute, reconcile, close, activate detectors, mark tickets authoritative, or change rollback acceptance without the reviewed AegisOps record and reviewer path."
  "After break-glass use, operators must rotate or invalidate the affected secret, capture reload or restart evidence, run the relevant readiness or refusal check, and retain the follow-up owner before normal operation resumes."
  'Rollback and restore escalation must stay cross-linked to `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md`, `docs/deployment/operational-evidence-handoff-pack.md`, and `docs/runbook.md`.'
  "Escalate to rollback when runtime, detector, coordination, assistant, or evidence drift cannot be corrected inside the reviewed maintenance or health-review window without widening scope."
  "Escalate to restore when authoritative approval, evidence, execution, or reconciliation records are missing, orphaned, partially restored, mixed-snapshot, or no longer attributable to the selected restore point."
  "Rejected, forbidden, failed, rollback, or restore-failure paths must retain the refusal reason and clean-state proof; it is not enough to record that an exception occurred."
  "Evidence collection must remain operator-readable and compact: record the event, named operator, affected path, authoritative AegisOps record ids, repository revision or release identifier, command or inspection output, refusal reason when present, clean-state proof, follow-up owner, and next review."
  'Use repo-relative commands, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, and `<support-evidence-note.md>`.'
  'Verify this playbook with `scripts/verify-support-playbook-break-glass-rehearsal.sh`.'
  'Negative validation for the verifier is `scripts/test-verify-support-playbook-break-glass-rehearsal.sh`.'
)

for phrase in "${required_playbook_phrases[@]}"; do
  require_phrase "${playbook_path}" "${phrase}" "support playbook statement"
done

require_phrase "${runbook_path}" 'For pilot support degradation, break-glass rehearsal, and operator-readable evidence expectations, use `docs/deployment/support-playbook-break-glass-rehearsal.md` and verify it with `scripts/verify-support-playbook-break-glass-rehearsal.sh`.' "runbook support playbook link"
require_phrase "${pilot_readiness_path}" 'The support playbook in `docs/deployment/support-playbook-break-glass-rehearsal.md` is the reviewed pilot degradation and break-glass rehearsal reference; pilot entry remains blocked if support expectations would require 24x7 coverage, customer-specific support terms, or emergency authority bypass.' "pilot readiness support playbook link"
require_phrase "${restore_path}" 'Support escalation from `docs/deployment/support-playbook-break-glass-rehearsal.md` must route rollback and restore decisions back to this release-gate rehearsal and retain refusal reason plus clean-state evidence for failed paths.' "restore rehearsal support playbook link"
require_phrase "${handoff_path}" 'Support playbook evidence from `docs/deployment/support-playbook-break-glass-rehearsal.md` may be retained in this handoff pack only as operator-readable evidence attached to reviewed AegisOps records.' "operational handoff support playbook link"

for forbidden in \
  "24x7 on-call is provided" \
  "SLA support is provided" \
  "customer-specific support contract is provided" \
  "emergency authority bypass is approved" \
  "break-glass may approve rollback acceptance" \
  "break-glass may approve" \
  "break-glass may execute" \
  "break-glass may reconcile" \
  "break-glass may close tickets" \
  "break-glass may close" \
  "break-glass may activate detectors" \
  "break-glass may deactivate detectors" \
  "break-glass may enable detectors" \
  "break-glass may mark tickets authoritative" \
  "break-glass may mark ticket state authoritative" \
  "break-glass may change rollback acceptance" \
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
  reject_phrase "${playbook_path}" "${forbidden}" "support playbook statement"
done

reject_workstation_paths "support playbook guidance" \
  "${playbook_path}" \
  "${runbook_path}" \
  "${pilot_readiness_path}" \
  "${restore_path}" \
  "${handoff_path}"

echo "Support playbook, break-glass rehearsal, escalation cross-links, and evidence expectations are present and bounded."
