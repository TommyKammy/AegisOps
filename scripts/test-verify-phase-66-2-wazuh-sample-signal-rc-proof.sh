#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    cat "${fail_stdout}" >&2
    exit 1
  fi

  if ! grep -Fiq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

copy_repo_path() {
  local target="$1"
  local relative_path="$2"

  mkdir -p "${target}/$(dirname "${relative_path}")"
  cp -p "${repo_root}/${relative_path}" "${target}/${relative_path}"
}

copy_valid_repo() {
  local target="$1"
  local path

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"

  for path in \
    "docs/phase-66-1-clean-host-rc-e2e-harness.md" \
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "docs/deployment/wazuh-manager-intake-binding-contract.md" \
    "docs/deployment/wazuh-source-health-projection-contract.md" \
    "docs/deployment/wazuh-authority-boundary-negative-tests.md" \
    "docs/phase-65-closeout-evaluation.md"; do
    copy_repo_path "${target}" "${path}"
  done

  for path in \
    "scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh" \
    "scripts/test-verify-phase-66-2-wazuh-sample-signal-rc-proof.sh" \
    "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh" \
    "scripts/verify-publishable-path-hygiene.sh"; do
    copy_repo_path "${target}" "${path}"
  done

  git -C "${target}" init -q
  git -C "${target}" config user.email "aegisops@example.invalid"
  git -C "${target}" config user.name "AegisOps Test"
  git -C "${target}" add README.md docs scripts control-plane/aegisops
  git -C "${target}" commit -q -m "fixture"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
}

comment_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E/<!-- $ENV{TEXT} -->/g' \
    "${target}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66.2 Wazuh sample signal RC proof"

missing_reference_repo="${workdir}/missing-reference"
copy_valid_repo "${missing_reference_repo}"
rm "${missing_reference_repo}/docs/deployment/wazuh-source-health-projection-contract.md"
assert_fails_with "${missing_reference_repo}" "Missing Phase 66.2 reference docs/deployment/wazuh-source-health-projection-contract.md"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 66\.2 Wazuh sample signal RC proof\]\(docs\/phase-66-2-wazuh-sample-signal-rc-proof\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical Phase 66.2 boundary bullet"

missing_authority_policy_baseline_repo="${workdir}/missing-authority-policy-baseline"
copy_valid_repo "${missing_authority_policy_baseline_repo}"
remove_doc_text "${missing_authority_policy_baseline_repo}" \
  "\`docs/phase-51-6-authority-boundary-negative-test-policy.md\`, "
assert_fails_with "${missing_authority_policy_baseline_repo}" "Missing required Phase 66.2 Wazuh sample signal proof term"

missing_signal_identity_repo="${workdir}/missing-signal-identity"
copy_valid_repo "${missing_signal_identity_repo}"
remove_doc_text "${missing_signal_identity_repo}" \
  "| \`sample_signal_id\` | Stable sample signal identifier. | Dashboard text or filenames cannot create signal identity. |"
assert_fails_with "${missing_signal_identity_repo}" "Missing Phase 66.2 sample signal evidence field"

commented_admission_repo="${workdir}/commented-admission"
copy_valid_repo "${commented_admission_repo}"
comment_doc_text "${commented_admission_repo}" \
  "| \`admission_record_id\` | AegisOps admission record for the sample signal. | Wazuh alerts remain candidate signals until admission. |"
assert_fails_with "${commented_admission_repo}" "Missing Phase 66.2 sample signal evidence field"

missing_source_health_repo="${workdir}/missing-source-health-term"
copy_valid_repo "${missing_source_health_repo}"
remove_doc_text "${missing_source_health_repo}" "manager, dashboard, indexer, intake, signal freshness, parser, volume, and credential posture"
assert_fails_with "${missing_source_health_repo}" "Missing Phase 66.2 source-health or admission term"

missing_source_health_citation_repo="${workdir}/missing-source-health-citation"
copy_valid_repo "${missing_source_health_citation_repo}"
remove_doc_text "${missing_source_health_citation_repo}" "The proof must cite \`docs/deployment/wazuh-source-health-projection-contract.md\`"
assert_fails_with "${missing_source_health_citation_repo}" "Missing Phase 66.2 source-health or admission term"

missing_intake_citation_repo="${workdir}/missing-intake-citation"
copy_valid_repo "${missing_intake_citation_repo}"
remove_doc_text "${missing_intake_citation_repo}" "The proof must cite \`docs/deployment/wazuh-manager-intake-binding-contract.md\`"
assert_fails_with "${missing_intake_citation_repo}" "Missing Phase 66.2 source-health or admission term"

missing_limitations_repo="${workdir}/missing-limitations"
copy_valid_repo "${missing_limitations_repo}"
remove_doc_text "${missing_limitations_repo}" \
  "It does not prove broad Wazuh detector parity, production customer telemetry import, production monitoring coverage, real design-partner success, source-native truth, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness."
assert_fails_with "${missing_limitations_repo}" "Missing Phase 66.2 accepted limitations boundary"

missing_verifier_script_repo="${workdir}/missing-verifier-script"
copy_valid_repo "${missing_verifier_script_repo}"
rm "${missing_verifier_script_repo}/scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"
assert_fails_with "${missing_verifier_script_repo}" "Missing Phase 66.2 verifier script scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"

mutable_repository_revision_repo="${workdir}/mutable-repository-revision"
copy_valid_repo "${mutable_repository_revision_repo}"
printf '%s\n' "repository_revision: main" >>"${mutable_repository_revision_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${mutable_repository_revision_repo}" "mutable repository revision detected"

remote_tracking_repository_revision_repo="${workdir}/remote-tracking-repository-revision"
copy_valid_repo "${remote_tracking_repository_revision_repo}"
printf '%s\n' "repository_revision: refs/remotes/origin/main" >>"${remote_tracking_repository_revision_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${remote_tracking_repository_revision_repo}" "mutable repository revision detected"

valid_repository_revision_repo="${workdir}/valid-repository-revision"
copy_valid_repo "${valid_repository_revision_repo}"
printf '%s\n' "repository_revision: 0123456789abcdef0123456789abcdef01234567" >>"${valid_repository_revision_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_passes "${valid_repository_revision_repo}"

invalid_wazuh_profile_repo="${workdir}/invalid-wazuh-profile"
copy_valid_repo "${invalid_wazuh_profile_repo}"
printf '%s\n' "wazuh_profile: enterprise-cluster" >>"${invalid_wazuh_profile_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${invalid_wazuh_profile_repo}" "invalid Wazuh profile detected"

valid_wazuh_profile_repo="${workdir}/valid-wazuh-profile"
copy_valid_repo "${valid_wazuh_profile_repo}"
printf '%s\n' "wazuh_profile: smb-single-node" >>"${valid_wazuh_profile_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_passes "${valid_wazuh_profile_repo}"

inferred_source_family_repo="${workdir}/inferred-source-family"
copy_valid_repo "${inferred_source_family_repo}"
printf '%s\n' "source_family: inferred from nearby prose" >>"${inferred_source_family_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${inferred_source_family_repo}" "inferred source-family value detected"

invalid_case_linking_posture_repo="${workdir}/invalid-case-linking-posture"
copy_valid_repo "${invalid_case_linking_posture_repo}"
printf '%s\n' "case_linking_posture: linked_by_wazuh_case_workflow" >>"${invalid_case_linking_posture_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${invalid_case_linking_posture_repo}" "invalid case-linking posture detected"

valid_case_linking_posture_repo="${workdir}/valid-case-linking-posture"
copy_valid_repo "${valid_case_linking_posture_repo}"
printf '%s\n' "case_linking_posture: linked_by_aegisops_case_workflow" >>"${valid_case_linking_posture_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_passes "${valid_case_linking_posture_repo}"

ga_ready_repo="${workdir}/ga-ready"
copy_valid_repo "${ga_ready_repo}"
printf '%s\n' "Phase 66.2 proves GA readiness." >>"${ga_ready_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${ga_ready_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

direct_ga_ready_repo="${workdir}/direct-ga-ready"
copy_valid_repo "${direct_ga_ready_repo}"
printf '%s\n' "This proof satisfies GA readiness." >>"${direct_ga_ready_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${direct_ga_ready_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

safe_gate_truth_repo="${workdir}/safe-gate-truth"
copy_valid_repo "${safe_gate_truth_repo}"
printf '%s\n' "Phase 66.2 confirms gate truth remains AegisOps-owned." >>"${safe_gate_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_passes "${safe_gate_truth_repo}"

rc_pass_repo="${workdir}/rc-pass"
copy_valid_repo "${rc_pass_repo}"
printf '%s\n' "Phase 66.2 passes RC." >>"${rc_pass_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${rc_pass_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

ga_ready_copular_repo="${workdir}/ga-ready-copular"
copy_valid_repo "${ga_ready_copular_repo}"
printf '%s\n' "Phase 66.2 is ready for GA." >>"${ga_ready_copular_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${ga_ready_copular_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

rc_ready_copular_repo="${workdir}/rc-ready-copular"
copy_valid_repo "${rc_ready_copular_repo}"
printf '%s\n' "Phase 66.2 is ready for RC." >>"${rc_ready_copular_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${rc_ready_copular_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

not_ga_ready_repo="${workdir}/not-ga-ready"
copy_valid_repo "${not_ga_ready_repo}"
printf '%s\n' "Phase 66.2 is not ready for GA." >>"${not_ga_ready_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_passes "${not_ga_ready_repo}"

aegisops_rc_ready_repo="${workdir}/aegisops-rc-ready"
copy_valid_repo "${aegisops_rc_ready_repo}"
printf '%s\n' "AegisOps is ready for RC." >>"${aegisops_rc_ready_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${aegisops_rc_ready_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

design_partner_success_repo="${workdir}/design-partner-success"
copy_valid_repo "${design_partner_success_repo}"
printf '%s\n' "Phase 66.2 proves real design-partner success." >>"${design_partner_success_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${design_partner_success_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

phase66_closeout_repo="${workdir}/phase66-closeout"
copy_valid_repo "${phase66_closeout_repo}"
printf '%s\n' "Phase 66.2 proves Phase 66 closeout." >>"${phase66_closeout_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${phase66_closeout_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

readme_overclaim_repo="${workdir}/readme-overclaim"
copy_valid_repo "${readme_overclaim_repo}"
printf '%s\n' "Phase 66.2 proves broad SIEM parity." >>"${readme_overclaim_repo}/README.md"
assert_fails_with "${readme_overclaim_repo}" "Forbidden Phase 66.2 README claim matched"

wazuh_truth_repo="${workdir}/wazuh-truth"
copy_valid_repo "${wazuh_truth_repo}"
printf '%s\n' "Wazuh becomes AegisOps case truth after this proof." >>"${wazuh_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

plural_wazuh_truth_repo="${workdir}/plural-wazuh-truth"
copy_valid_repo "${plural_wazuh_truth_repo}"
printf '%s\n' "Wazuh alerts become AegisOps alert truth after admission." >>"${plural_wazuh_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${plural_wazuh_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_evidence_truth_repo="${workdir}/wazuh-evidence-truth"
copy_valid_repo "${wazuh_evidence_truth_repo}"
printf '%s\n' "Wazuh alerts are evidence truth." >>"${wazuh_evidence_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_evidence_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_alert_id_truth_repo="${workdir}/wazuh-alert-id-truth"
copy_valid_repo "${wazuh_alert_id_truth_repo}"
printf '%s\n' "Wazuh alert ids are AegisOps alert truth." >>"${wazuh_alert_id_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_alert_id_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_origin_input_truth_repo="${workdir}/wazuh-origin-input-truth"
copy_valid_repo "${wazuh_origin_input_truth_repo}"
printf '%s\n' "Wazuh-origin input is AegisOps case truth before admission." >>"${wazuh_origin_input_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_origin_input_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

source_admission_truth_repo="${workdir}/source-admission-truth"
copy_valid_repo "${source_admission_truth_repo}"
printf '%s\n' "Wazuh is source admission truth." >>"${source_admission_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${source_admission_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_manager_state_release_truth_repo="${workdir}/wazuh-manager-state-release-truth"
copy_valid_repo "${wazuh_manager_state_release_truth_repo}"
printf '%s\n' "Wazuh manager state is release truth." >>"${wazuh_manager_state_release_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_manager_state_release_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_dashboard_state_gate_truth_repo="${workdir}/wazuh-dashboard-state-gate-truth"
copy_valid_repo "${wazuh_dashboard_state_gate_truth_repo}"
printf '%s\n' "Wazuh dashboard state is gate truth." >>"${wazuh_dashboard_state_gate_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_dashboard_state_gate_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_indexer_contents_release_truth_repo="${workdir}/wazuh-indexer-contents-release-truth"
copy_valid_repo "${wazuh_indexer_contents_release_truth_repo}"
printf '%s\n' "Wazuh indexer contents are release truth." >>"${wazuh_indexer_contents_release_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_indexer_contents_release_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

webhook_acknowledgements_release_truth_repo="${workdir}/webhook-acknowledgements-release-truth"
copy_valid_repo "${webhook_acknowledgements_release_truth_repo}"
printf '%s\n' "Webhook acknowledgements are release truth." >>"${webhook_acknowledgements_release_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${webhook_acknowledgements_release_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

verifier_readiness_repo="${workdir}/verifier-readiness"
copy_valid_repo "${verifier_readiness_repo}"
printf '%s\n' "Verifier output proves readiness for Phase 66.2." >>"${verifier_readiness_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${verifier_readiness_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

source_native_truth_repo="${workdir}/source-native-truth"
copy_valid_repo "${source_native_truth_repo}"
printf '%s\n' "Source-native truth is accepted for the Wazuh sample signal proof." >>"${source_native_truth_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${source_native_truth_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

broad_siem_direct_repo="${workdir}/broad-siem-direct"
copy_valid_repo "${broad_siem_direct_repo}"
printf '%s\n' "The proof achieves broad SIEM parity for this path." >>"${broad_siem_direct_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${broad_siem_direct_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

broad_wazuh_direct_repo="${workdir}/broad-wazuh-direct"
copy_valid_repo "${broad_wazuh_direct_repo}"
printf '%s\n' "The proof achieves broad Wazuh detector parity for this path." >>"${broad_wazuh_direct_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${broad_wazuh_direct_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

production_telemetry_repo="${workdir}/production-telemetry"
copy_valid_repo "${production_telemetry_repo}"
printf '%s\n' "This proof proves production customer telemetry import for this path." >>"${production_telemetry_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${production_telemetry_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

production_monitoring_confirmation_repo="${workdir}/production-monitoring-confirmation"
copy_valid_repo "${production_monitoring_confirmation_repo}"
printf '%s\n' "Phase 66.2 confirms production monitoring coverage." >>"${production_monitoring_confirmation_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${production_monitoring_confirmation_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

production_monitoring_limitation_repo="${workdir}/production-monitoring-limitation"
copy_valid_repo "${production_monitoring_limitation_repo}"
printf '%s\n' "Phase 66.2 confirms production monitoring remains out of scope." >>"${production_monitoring_limitation_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_passes "${production_monitoring_limitation_repo}"

wazuh_state_authority_repo="${workdir}/wazuh-state-authority"
copy_valid_repo "${wazuh_state_authority_repo}"
printf '%s\n' "Wazuh dashboard state approves the release gate." >>"${wazuh_state_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_state_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_action_request_authority_repo="${workdir}/wazuh-action-request-authority"
copy_valid_repo "${wazuh_action_request_authority_repo}"
printf '%s\n' "Wazuh alerts approve action requests." >>"${wazuh_action_request_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_action_request_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_alert_promotion_authority_repo="${workdir}/wazuh-alert-promotion-authority"
copy_valid_repo "${wazuh_alert_promotion_authority_repo}"
printf '%s\n' "Wazuh alerts promote cases." >>"${wazuh_alert_promotion_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_alert_promotion_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_alert_status_authority_repo="${workdir}/wazuh-alert-status-authority"
copy_valid_repo "${wazuh_alert_status_authority_repo}"
printf '%s\n' "Wazuh alert status approves the release gate." >>"${wazuh_alert_status_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_alert_status_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

webhook_ack_authority_repo="${workdir}/webhook-ack-authority"
copy_valid_repo "${webhook_ack_authority_repo}"
printf '%s\n' "Webhook acknowledgement approves the release gate." >>"${webhook_ack_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${webhook_ack_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

wazuh_source_health_authority_repo="${workdir}/wazuh-source-health-authority"
copy_valid_repo "${wazuh_source_health_authority_repo}"
printf '%s\n' "Wazuh source health approves the release gate." >>"${wazuh_source_health_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${wazuh_source_health_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

source_health_projection_authority_repo="${workdir}/source-health-projection-authority"
copy_valid_repo "${source_health_projection_authority_repo}"
printf '%s\n' "Source-health projection approves the release gate." >>"${source_health_projection_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${source_health_projection_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

generated_config_authority_repo="${workdir}/generated-config-authority"
copy_valid_repo "${generated_config_authority_repo}"
printf '%s\n' "Generated config approves the release gate." >>"${generated_config_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${generated_config_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

ai_authority_repo="${workdir}/ai-authority"
copy_valid_repo "${ai_authority_repo}"
printf '%s\n' "AI output approves the release gate." >>"${ai_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${ai_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

browser_authority_repo="${workdir}/browser-authority"
copy_valid_repo "${browser_authority_repo}"
printf '%s\n' "Browser state gates the release." >>"${browser_authority_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${browser_authority_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

dashboard_text_identity_repo="${workdir}/dashboard-text-identity"
copy_valid_repo "${dashboard_text_identity_repo}"
printf '%s\n' "Dashboard text creates signal identity for the proof." >>"${dashboard_text_identity_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${dashboard_text_identity_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

filenames_identity_repo="${workdir}/filenames-identity"
copy_valid_repo "${filenames_identity_repo}"
printf '%s\n' "Filenames create signal identity for the proof." >>"${filenames_identity_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${filenames_identity_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

raw_forwarded_headers_provenance_repo="${workdir}/raw-forwarded-headers-provenance"
copy_valid_repo "${raw_forwarded_headers_provenance_repo}"
printf '%s\n' "Raw forwarded headers prove provenance for the sample signal." >>"${raw_forwarded_headers_provenance_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${raw_forwarded_headers_provenance_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

inferred_linkage_provenance_repo="${workdir}/inferred-linkage-provenance"
copy_valid_repo "${inferred_linkage_provenance_repo}"
printf '%s\n' "Inferred linkage proves provenance for the sample signal." >>"${inferred_linkage_provenance_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${inferred_linkage_provenance_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

direct_intake_shortcut_repo="${workdir}/direct-intake-shortcut"
copy_valid_repo "${direct_intake_shortcut_repo}"
printf '%s\n' "Direct intake paths prove intake binding." >>"${direct_intake_shortcut_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${direct_intake_shortcut_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

ad_hoc_intake_shortcut_repo="${workdir}/ad-hoc-intake-shortcut"
copy_valid_repo "${ad_hoc_intake_shortcut_repo}"
printf '%s\n' "Ad hoc intake paths satisfy intake binding." >>"${ad_hoc_intake_shortcut_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${ad_hoc_intake_shortcut_repo}" "Forbidden Phase 66.2 Wazuh sample signal RC proof claim matched"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "api_key: abcdefghijklmnop" >>"${secret_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${secret_repo}" "production secret-looking value detected"

secret_key_repo="${workdir}/secret-key"
copy_valid_repo "${secret_key_repo}"
printf '%s\n' "secret_key: abcdefghijklmnop" >>"${secret_key_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${secret_key_repo}" "production secret-looking value detected"

private_key_repo="${workdir}/private-key"
copy_valid_repo "${private_key_repo}"
printf '%s\n' "private_key: abcdefghijklmnop" >>"${private_key_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${private_key_repo}" "production secret-looking value detected"

missing_sample_signal_id_repo="${workdir}/missing-sample-signal-id-value"
copy_valid_repo "${missing_sample_signal_id_repo}"
printf '%s\n' "sample_signal_id: missing" >>"${missing_sample_signal_id_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${missing_sample_signal_id_repo}" "missing required evidence value detected"

missing_journey_run_id_repo="${workdir}/missing-journey-run-id-value"
copy_valid_repo "${missing_journey_run_id_repo}"
printf '%s\n' "journey_run_id: missing" >>"${missing_journey_run_id_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${missing_journey_run_id_repo}" "missing required evidence value detected"

missing_repository_revision_repo="${workdir}/missing-repository-revision-value"
copy_valid_repo "${missing_repository_revision_repo}"
printf '%s\n' "repository_revision: missing" >>"${missing_repository_revision_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${missing_repository_revision_repo}" "missing required evidence value detected"

missing_admission_record_repo="${workdir}/missing-admission-record-value"
copy_valid_repo "${missing_admission_record_repo}"
printf '%s\n' "admission_record_id: missing" >>"${missing_admission_record_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${missing_admission_record_repo}" "missing required evidence value detected"

missing_provenance_repo="${workdir}/missing-provenance-value"
copy_valid_repo "${missing_provenance_repo}"
printf '%s\n' "provenance_reference: missing" >>"${missing_provenance_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${missing_provenance_repo}" "missing required evidence value detected"

hidden_limitation_references_repo="${workdir}/hidden-limitation-references"
copy_valid_repo "${hidden_limitation_references_repo}"
printf '%s\n' "limitation_references: hidden in source-health text" >>"${hidden_limitation_references_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${hidden_limitation_references_repo}" "hidden limitation references detected"

customer_private_repo="${workdir}/customer-private"
copy_valid_repo "${customer_private_repo}"
printf '%s\n' "The proof includes customer-private alert export." >>"${customer_private_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

customer_private_negation_repo="${workdir}/customer-private-negation"
copy_valid_repo "${customer_private_negation_repo}"
printf '%s\n' "The proof contains customer-private alert export without redaction." >>"${customer_private_negation_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${customer_private_negation_repo}" "customer-private data detected"

customer_private_bare_repo="${workdir}/customer-private-bare"
copy_valid_repo "${customer_private_bare_repo}"
printf '%s\n' "customer-private data: Acme incident payload" >>"${customer_private_bare_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${customer_private_bare_repo}" "customer-private data detected"

customer_private_prohibition_repo="${workdir}/customer-private-prohibition"
copy_valid_repo "${customer_private_prohibition_repo}"
printf '%s\n' "The proof must not include customer-private data: Acme incident payload." >>"${customer_private_prohibition_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${customer_private_prohibition_repo}" "customer-private data detected"

local_path_repo="${workdir}/local-path"
copy_valid_repo "${local_path_repo}"
printf 'Evidence path: /%s/example/aegisops/private\n' "Users" >>"${local_path_repo}/docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
assert_fails_with "${local_path_repo}" "absolute path"

echo "Phase 66.2 Wazuh sample signal RC proof verifier self-test passed."
