#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
criteria_path="${repo_root}/docs/deployment/pilot-pause-rollback-exit-criteria.md"
runbook_path="${repo_root}/docs/runbook.md"
pilot_checklist_path="${repo_root}/docs/deployment/pilot-readiness-checklist.md"
support_path="${repo_root}/docs/deployment/support-playbook-break-glass-rehearsal.md"
operator_packet_path="${repo_root}/docs/deployment/operator-training-handoff-packet.md"
release_handoff_path="${repo_root}/docs/deployment/release-handoff-evidence-package.md"
operational_handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
restore_path="${repo_root}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
verifier_test_path="${repo_root}/scripts/test-verify-pilot-pause-rollback-exit-criteria.sh"

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
  windows_home_pattern='[A-Za-z]:\\'"Users"'\\[^[:space:])>]+'
  workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"

  if grep -Eq "${workstation_local_path_pattern}" "$@"; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi
}

require_file "${criteria_path}" "pilot pause rollback exit criteria document"
require_file "${runbook_path}" "runbook"
require_file "${pilot_checklist_path}" "pilot readiness checklist"
require_file "${support_path}" "support playbook"
require_file "${operator_packet_path}" "operator training packet"
require_file "${release_handoff_path}" "release handoff package"
require_file "${operational_handoff_path}" "operational evidence handoff pack"
require_file "${restore_path}" "restore rollback upgrade evidence rehearsal"
require_file "${verifier_test_path}" "pilot pause rollback exit criteria verifier tests"

required_headings=(
  "# Pilot Pause, Rollback, and Exit Criteria"
  "## 1. Purpose and Boundary"
  "## 2. Decision Record"
  "## 3. Pilot Pause Criteria"
  "## 4. Rollback Criteria"
  "## 5. Exit and Success Criteria"
  "## 6. Unresolved Limitations and Next-Roadmap Input"
  "## 7. Operator and Support Signoff Checklist"
  "## 8. Verification"
  "## 9. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${criteria_path}" "${heading}" "pilot pause rollback exit criteria heading"
done

required_criteria_phrases=(
  "This document defines reviewed pause, rollback, continue, exit, unresolved-limitation, and next-roadmap capture criteria for the single-customer pilot."
  "The decision surface is operational and reviewable. It is not a customer commercial terms sheet, public launch checklist, SLA acceptance record, multi-customer rollout gate, or multi-tenant expansion plan."
  "Pilot pause, rollback, continue, and exit decisions remain subordinate to AegisOps authoritative records, the pilot readiness decision, support playbook evidence, operator handoff evidence, and the restore, rollback, and upgrade release-gate rehearsal."
  "the decision: continue, pause, rollback, exit-success, exit-no-go, or capture-next-roadmap-input; and"
  "The decision must use directly linked AegisOps records and retained evidence."
  "Pause the pilot and keep normal operator use blocked when any of the following are true:"
  "support expectations would require 24x7 coverage, customer-specific paid support terms, emergency authority bypass, direct backend access, or customer-private secret exposure;"
  "Pause is a reviewed hold state, not a silent success, informal support escalation, commercial renegotiation, or permission to keep operating with guessed prerequisites."
  "Escalate to rollback when the pilot cannot continue or pause safely on the current release because runtime, detector, coordination, assistant, support, evidence, or handoff drift would leave reviewed records ambiguous or untrustworthy."
  'Rollback must align with `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md` and retain:'
  "clean-state proof that no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived the attempt."
  "Rollback does not authorize direct source-side mutation, vendor-specific backup product dependency, HA choreography, direct backend exposure, optional-extension launch gates, ticket-system authority, assistant-owned workflow decisions, or customer-private production access."
  "Exit-success is allowed only when the reviewed pilot record shows that the single-customer operating path stayed bounded and trustworthy for the reviewed pilot window."
  "operator and support signoff that the queue, case, action-review, reviewed-record, non-authority, pause, rollback, and evidence handoff paths are understood; and"
  "Exit-no-go is required when the pilot cannot prove those criteria, when rollback or clean-state evidence is missing after a failed path, or when the outcome would depend on customer commercial terms, public launch readiness, multi-customer rollout assumptions, or multi-tenant expansion criteria."
  "Unresolved limitations must be handled as reviewed records with a disposition of block, accept-with-owner, rollback, disable, support-follow-up, or capture-next-roadmap-input."
  "Next-roadmap input may capture candidate follow-up work from the pilot, but it must remain separate from Phase 43 acceptance."
  "Captured input must not turn customer commercial terms, public launch checklist items, multi-customer rollout requirements, multi-tenant expansion criteria, optional-extension launch gates, or broad support promises into current pilot scope."
  "Before continuing after a pause, accepting rollback completion, or recording exit-success, operator and support signoff must confirm:"
  "the support playbook was reviewed for degradation and break-glass handling;"
  "the operator training packet was reviewed for queue, case, action-review, reviewed-record, non-authority, and evidence handoff practice;"
  "no signoff relies on workstation-local absolute paths, live secrets, placeholder credentials, raw forwarded headers, ticket authority, assistant authority, optional-extension health, or inferred scope."
  'Verify this criteria document with `scripts/verify-pilot-pause-rollback-exit-criteria.sh`.'
  'Negative validation for the verifier is `scripts/test-verify-pilot-pause-rollback-exit-criteria.sh`.'
  "Customer commercial terms, formal SLA commitments, public launch checklist ownership, hosted release channels, multi-customer rollout, multi-tenant expansion criteria, direct customer-private production access, direct backend exposure, optional-extension launch gates, ticket-system authority, assistant-owned workflow authority, and broad support promises beyond the reviewed business-hours single-customer pilot are out of scope."
)

for phrase in "${required_criteria_phrases[@]}"; do
  require_phrase "${criteria_path}" "${phrase}" "pilot pause rollback exit criteria statement"
done

require_phrase "${runbook_path}" 'Before continuing, pausing, rolling back, or exiting a single-customer pilot, review `docs/deployment/pilot-pause-rollback-exit-criteria.md` and verify it with `scripts/verify-pilot-pause-rollback-exit-criteria.sh` so pause criteria, rollback criteria, exit criteria, unresolved limitations, next-roadmap input, and operator/support signoff remain bounded to Phase 43.' "runbook pilot pause rollback exit criteria link"
require_phrase "${pilot_checklist_path}" 'Pilot pause, rollback, and exit decisions must use `docs/deployment/pilot-pause-rollback-exit-criteria.md`; entry readiness alone is not exit-success, rollback acceptance, or permission to continue after a paused or degraded pilot.' "pilot readiness pause rollback exit criteria link"
require_phrase "${support_path}" 'Pilot pause, rollback, and exit decisions must use `docs/deployment/pilot-pause-rollback-exit-criteria.md` so support degradation, break-glass evidence, rollback escalation, unresolved limitations, and next-roadmap input remain reviewed and bounded.' "support playbook pause rollback exit criteria link"
require_phrase "${operator_packet_path}" 'For pilot pause, rollback, continue, or exit signoff, operators must use `docs/deployment/pilot-pause-rollback-exit-criteria.md` after completing the queue, case, action-review, reviewed-record, non-authority, and evidence handoff walkthrough.' "operator training pause rollback exit criteria link"
require_phrase "${release_handoff_path}" 'Pilot exit-success, exit-no-go, pause, continue, and rollback decisions must point to `docs/deployment/pilot-pause-rollback-exit-criteria.md` instead of treating release handoff alone as pilot success.' "release handoff pause rollback exit criteria link"
require_phrase "${operational_handoff_path}" 'Pilot pause, rollback, continue, and exit evidence must use `docs/deployment/pilot-pause-rollback-exit-criteria.md` as the reviewed operator/support decision surface for unresolved limitations and next-roadmap input capture.' "operational handoff pause rollback exit criteria link"
require_phrase "${restore_path}" 'Pilot rollback acceptance must stay aligned to `docs/deployment/pilot-pause-rollback-exit-criteria.md`; a same-day rollback decision is not accepted for pilot continuation or exit until operator/support signoff, refusal reason when applicable, and clean-state evidence are retained.' "restore rollback rehearsal pause rollback exit criteria link"

for doc_path in \
  "${criteria_path}" \
  "${pilot_checklist_path}" \
  "${support_path}" \
  "${operator_packet_path}" \
  "${release_handoff_path}" \
  "${operational_handoff_path}" \
  "${restore_path}"; do
  for forbidden in \
    "customer commercial terms are approved" \
    "public launch checklist is approved" \
    "multi-tenant expansion is approved" \
    "multi-customer rollout is approved" \
    "24x7 support is promised" \
    "SLA is promised" \
    "ticket status is authoritative" \
    "assistant may approve" \
    "assistant may execute"; do
    reject_phrase "${doc_path}" "${forbidden}" "pilot pause rollback exit criteria statement"
  done
done

reject_workstation_paths "pilot pause rollback exit guidance" \
  "${criteria_path}" \
  "${runbook_path}" \
  "${pilot_checklist_path}" \
  "${support_path}" \
  "${operator_packet_path}" \
  "${release_handoff_path}" \
  "${operational_handoff_path}" \
  "${restore_path}"

echo "Pilot pause, rollback, exit, unresolved limitation, next-roadmap, and operator/support signoff criteria are present and bounded."
