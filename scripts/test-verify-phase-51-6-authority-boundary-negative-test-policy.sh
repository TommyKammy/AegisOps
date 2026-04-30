#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' "# AegisOps" "See [Phase 51.6 authority-boundary negative-test policy](docs/phase-51-6-authority-boundary-negative-test-policy.md)." >"${target}/README.md"
  cp "${repo_root}/docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "${target}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
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

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

remove_text_from_policy() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
}

replace_text_in_policy() {
  local target="$1"
  local old_text="$2"
  local new_text="$3"

  OLD_TEXT="${old_text}" NEW_TEXT="${new_text}" perl -0pi -e 's/\Q$ENV{OLD_TEXT}\E/$ENV{NEW_TEXT}/g' \
    "${target}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

alternate_date_repo="${workdir}/alternate-date"
create_valid_repo "${alternate_date_repo}"
replace_text_in_policy \
  "${alternate_date_repo}" \
  "- **Date**: 2026-04-30" \
  "- **Date**: 2026-04-29"
assert_passes "${alternate_date_repo}"

invalid_date_repo="${workdir}/invalid-date"
create_valid_repo "${invalid_date_repo}"
replace_text_in_policy \
  "${invalid_date_repo}" \
  "- **Date**: 2026-04-30" \
  "- **Date**: May 1, 2026"
assert_fails_with \
  "${invalid_date_repo}" \
  "Missing or invalid Phase 51.6 authority-boundary negative-test policy date line (- **Date**: YYYY-MM-DD)."

missing_policy_repo="${workdir}/missing-policy"
create_valid_repo "${missing_policy_repo}"
rm "${missing_policy_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${missing_policy_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy"

missing_ai_repo="${workdir}/missing-ai"
create_valid_repo "${missing_ai_repo}"
remove_text_from_policy "${missing_ai_repo}" \
  "| AI | AI output, tool suggestions, summaries, or recommendations are presented as approval, execution, reconciliation, case closure, detector activation, or source truth. | Reject the shortcut and require an explicit AegisOps record, human decision, or reviewed prerequisite. |"
assert_fails_with \
  "${missing_ai_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | AI |"

missing_wazuh_repo="${workdir}/missing-wazuh"
create_valid_repo "${missing_wazuh_repo}"
remove_text_from_policy "${missing_wazuh_repo}" \
  "| Wazuh | Wazuh alert, rule, manager, decoder, status, or timestamp state is presented as AegisOps alert, case, evidence, reconciliation, release, or gate truth without explicit admission and linkage. | Reject the shortcut and require an admitted AegisOps record linked to the Wazuh signal. |"
assert_fails_with \
  "${missing_wazuh_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Wazuh |"

missing_shuffle_repo="${workdir}/missing-shuffle"
create_valid_repo "${missing_shuffle_repo}"
remove_text_from_policy "${missing_shuffle_repo}" \
  "| Shuffle | Shuffle workflow success, failure, retry, payload, or callback state is presented as AegisOps execution receipt, reconciliation, case closure, release, or gate truth without AegisOps approval, action intent, receipt, and reconciliation records. | Reject the shortcut and keep reconciliation open or mismatched until the AegisOps record chain closes it. |"
assert_fails_with \
  "${missing_shuffle_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Shuffle |"

missing_tickets_repo="${workdir}/missing-tickets"
create_valid_repo "${missing_tickets_repo}"
remove_text_from_policy "${missing_tickets_repo}" \
  "| Tickets | Ticket open, closed, escalated, assigned, commented, or SLA state is presented as AegisOps case, approval, reconciliation, limitation, release, or gate truth. | Reject the shortcut and treat the ticket as coordination context linked to an authoritative AegisOps record. |"
assert_fails_with \
  "${missing_tickets_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Tickets |"

missing_endpoint_repo="${workdir}/missing-endpoint"
create_valid_repo "${missing_endpoint_repo}"
remove_text_from_policy "${missing_endpoint_repo}" \
  "| Endpoint evidence | Endpoint evidence, host facts, agent state, file paths, process data, or local collector status is presented as AegisOps evidence or source truth without reviewed custody, parser, and record linkage. | Reject the shortcut and require an AegisOps evidence record with custody and scope binding. |"
assert_fails_with \
  "${missing_endpoint_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Endpoint evidence |"

missing_network_repo="${workdir}/missing-network"
create_valid_repo "${missing_network_repo}"
remove_text_from_policy "${missing_network_repo}" \
  "| Network evidence | Network evidence, flow state, packet metadata, proxy logs, Suricata output, or external telemetry is presented as AegisOps evidence or source truth without reviewed custody, parser, and record linkage. | Reject the shortcut and require an AegisOps evidence record with custody and scope binding. |"
assert_fails_with \
  "${missing_network_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Network evidence |"

missing_evidence_systems_repo="${workdir}/missing-evidence-systems"
create_valid_repo "${missing_evidence_systems_repo}"
remove_text_from_policy "${missing_evidence_systems_repo}" \
  "| Evidence systems | External evidence-system status, retention, export, report, or custody text is presented as AegisOps evidence, release, gate, or production truth without explicit binding to the AegisOps evidence record. | Reject the shortcut and repair or refuse the projection instead of redefining truth around the external system. |"
assert_fails_with \
  "${missing_evidence_systems_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Evidence systems |"

missing_browser_repo="${workdir}/missing-browser"
create_valid_repo "${missing_browser_repo}"
remove_text_from_policy "${missing_browser_repo}" \
  "| Browser state | Browser URL, route state, local storage, session storage, cookie state, DOM text, or client navigation state is presented as AegisOps workflow truth. | Reject the shortcut and reload or recalculate from authoritative AegisOps records. |"
assert_fails_with \
  "${missing_browser_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Browser state |"

missing_ui_cache_repo="${workdir}/missing-ui-cache"
create_valid_repo "${missing_ui_cache_repo}"
remove_text_from_policy "${missing_ui_cache_repo}" \
  "| UI cache | Client cache, optimistic update, badge, counter, detail DTO, projection, or stale refresh result is presented as AegisOps workflow truth. | Reject the shortcut and repair the derived surface from authoritative AegisOps records. |"
assert_fails_with \
  "${missing_ui_cache_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | UI cache |"

missing_downstream_repo="${workdir}/missing-downstream"
create_valid_repo "${missing_downstream_repo}"
remove_text_from_policy "${missing_downstream_repo}" \
  "| Downstream receipts | Downstream receipt, webhook acknowledgement, adapter response, export receipt, support bundle receipt, or delivery receipt is presented as AegisOps reconciliation or closeout truth without AegisOps reconciliation. | Reject the shortcut and require the AegisOps reconciliation record or mismatch path. |"
assert_fails_with \
  "${missing_downstream_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Downstream receipts |"

missing_demo_repo="${workdir}/missing-demo"
create_valid_repo "${missing_demo_repo}"
remove_text_from_policy "${missing_demo_repo}" \
  "| Demo data | Seed data, sample fixture, demo persona, synthetic event, example receipt, fake secret, TODO value, or placeholder credential is presented as production truth. | Reject the shortcut and require trusted production binding, real credential custody, or an explicit demo-only refusal. |"
assert_fails_with \
  "${missing_demo_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: | Demo data |"

missing_citation_repo="${workdir}/missing-citation-rule"
create_valid_repo "${missing_citation_repo}"
remove_text_from_policy "${missing_citation_repo}" \
  "Any later issue that adds breadth for AI, Wazuh, Shuffle, tickets, endpoint evidence, network evidence, external evidence systems, browser state, UI cache, downstream receipts, or demo data must cite this policy and name the exact negative-test class it preserves."
assert_fails_with \
  "${missing_citation_repo}" \
  "Missing Phase 51.6 authority-boundary negative-test policy statement: Any later issue that adds breadth"

ai_approval_repo="${workdir}/ai-approval"
create_valid_repo "${ai_approval_repo}"
printf '%s\n' "AI may approve actions." \
  >>"${ai_approval_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${ai_approval_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: AI may approve actions"

ai_approval_variant_repo="${workdir}/ai-approval-variant"
create_valid_repo "${ai_approval_variant_repo}"
printf '%s\n' "  ai   MAY approve actions  " \
  >>"${ai_approval_variant_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${ai_approval_variant_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: AI may approve actions"

ai_reconciliation_repo="${workdir}/ai-reconciliation"
create_valid_repo "${ai_reconciliation_repo}"
printf '%s\n' "AI may reconcile execution." \
  >>"${ai_reconciliation_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${ai_reconciliation_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: AI may reconcile execution"

wazuh_close_repo="${workdir}/wazuh-close"
create_valid_repo "${wazuh_close_repo}"
printf '%s\n' "Wazuh alert status may close AegisOps records." \
  >>"${wazuh_close_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${wazuh_close_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: Wazuh alert status may close AegisOps records"

wazuh_gate_repo="${workdir}/wazuh-gate"
create_valid_repo "${wazuh_gate_repo}"
printf '%s\n' "Wazuh alert status may gate AegisOps records." \
  >>"${wazuh_gate_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${wazuh_gate_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: Wazuh alert status may gate AegisOps records"

shuffle_reconcile_repo="${workdir}/shuffle-reconcile"
create_valid_repo "${shuffle_reconcile_repo}"
printf '%s\n' "Shuffle workflow success may reconcile AegisOps records." \
  >>"${shuffle_reconcile_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${shuffle_reconcile_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: Shuffle workflow success may reconcile AegisOps records"

shuffle_release_repo="${workdir}/shuffle-release"
create_valid_repo "${shuffle_release_repo}"
printf '%s\n' "Shuffle may release AegisOps records." \
  >>"${shuffle_release_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${shuffle_release_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: Shuffle may release AegisOps records"

ticket_approve_repo="${workdir}/ticket-approve"
create_valid_repo "${ticket_approve_repo}"
printf '%s\n' "Ticket may approve." \
  >>"${ticket_approve_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${ticket_approve_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: Ticket may approve"

downstream_closeout_repo="${workdir}/downstream-closeout"
create_valid_repo "${downstream_closeout_repo}"
printf '%s\n' "Downstream may close out." \
  >>"${downstream_closeout_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${downstream_closeout_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy claim: Downstream may close out"

workstation_path_repo="${workdir}/workstation-local-path"
create_valid_repo "${workstation_path_repo}"
workstation_path="$(printf '/%s/%s/authority-policy.md' "Users" "example")"
printf '%s\n' "Policy path:file://${workstation_path}" \
  >>"${workstation_path_repo}/docs/phase-51-6-authority-boundary-negative-test-policy.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 51.6 authority-boundary negative-test policy: workstation-local absolute path detected"

raw_readme_path_repo="${workdir}/raw-readme-path"
create_valid_repo "${raw_readme_path_repo}"
printf '%s\n' "# AegisOps" "See docs/phase-51-6-authority-boundary-negative-test-policy.md." >"${raw_readme_path_repo}/README.md"
assert_fails_with \
  "${raw_readme_path_repo}" \
  "README must link the Phase 51.6 authority-boundary negative-test policy."

echo "Phase 51.6 authority-boundary negative-test policy verifier tests passed."
