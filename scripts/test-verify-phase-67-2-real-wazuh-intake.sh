#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-67-2-real-wazuh-intake.sh"
workdir="$(mktemp -d)"
trap 'chmod -R u+w "${workdir}" 2>/dev/null || true; rm -rf "${workdir}"' EXIT

copy_fixture() {
  local target="$1"

  mkdir -p \
    "${target}/control-plane/deployment" \
    "${target}/control-plane/aegisops/control_plane/ingestion" \
    "${target}/control-plane/tests/fixtures/wazuh" \
    "${target}/.github/workflows"
  cp -R \
    "${repo_root}/control-plane/deployment/phase-67-integration-lab" \
    "${target}/control-plane/deployment/"
  cp \
    "${repo_root}/control-plane/aegisops/control_plane/reviewed_slice_policy.py" \
    "${target}/control-plane/aegisops/control_plane/reviewed_slice_policy.py"
  cp \
    "${repo_root}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py" \
    "${target}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py"
  cp \
    "${repo_root}/control-plane/tests/test_phase67_2_real_wazuh_intake.py" \
    "${target}/control-plane/tests/test_phase67_2_real_wazuh_intake.py"
  cp \
    "${repo_root}/control-plane/tests/fixtures/wazuh/phase67-real-wazuh-ssh-auth-failure-alert.json" \
    "${target}/control-plane/tests/fixtures/wazuh/phase67-real-wazuh-ssh-auth-failure-alert.json"
  cp \
    "${repo_root}/.github/workflows/ci.yml" \
    "${target}/.github/workflows/ci.yml"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${workdir}/stdout" 2>"${workdir}/stderr"; then
    cat "${workdir}/stderr" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${workdir}/stdout" 2>"${workdir}/stderr"; then
    echo "Expected verifier failure for ${target}" >&2
    exit 1
  fi
  grep -F -- "${expected}" "${workdir}/stderr" >/dev/null || {
    echo "Expected verifier stderr to contain: ${expected}" >&2
    cat "${workdir}/stderr" >&2
    exit 1
  }
}

valid="${workdir}/valid"
copy_fixture "${valid}"
assert_passes "${valid}"

http_hook="${workdir}/http-hook"
copy_fixture "${http_hook}"
sed -i.bak \
  's#https://proxy:8443/intake/wazuh#http://proxy:8080/intake/wazuh#g' \
  "${http_hook}/control-plane/deployment/phase-67-integration-lab/wazuh/ossec-integration.xml"
assert_fails_with "${http_hook}" "<hook_url>https://proxy:8443/intake/wazuh</hook_url>"

unbounded_headers="${workdir}/unbounded-headers"
copy_fixture "${unbounded_headers}"
sed -i.bak \
  's/X-Forwarded-For \\$remote_addr/X-Forwarded-For \\$proxy_add_x_forwarded_for/' \
  "${unbounded_headers}/control-plane/deployment/phase-67-integration-lab/init.sh"
assert_fails_with \
  "${unbounded_headers}" \
  'proxy_set_header X-Forwarded-For \$remote_addr;'

rule_drift="${workdir}/rule-drift"
copy_fixture "${rule_drift}"
perl -0pi -e \
  's#<rule_id>5710</rule_id>#<rule_id>5711</rule_id>#' \
  "${rule_drift}/control-plane/deployment/phase-67-integration-lab/wazuh/ossec-integration.xml"
assert_fails_with "${rule_drift}" "<rule_id>5710</rule_id>"

secret_in_config="${workdir}/secret-in-config"
copy_fixture "${secret_in_config}"
perl -0pi -e \
  's#<api_key>file-bound</api_key>#<api_key>Bearer committed-secret</api_key>#' \
  "${secret_in_config}/control-plane/deployment/phase-67-integration-lab/wazuh/ossec-integration.xml"
assert_fails_with "${secret_in_config}" "<api_key>file-bound</api_key>"

source_family_drift="${workdir}/source-family-drift"
copy_fixture "${source_family_drift}"
sed -i.bak \
  's/SOURCE_FAMILY = \"wazuh_detection\"/SOURCE_FAMILY = \"github_audit\"/' \
  "${source_family_drift}/control-plane/deployment/phase-67-integration-lab/wazuh/aegisops_wazuh_integrator.py"
assert_fails_with "${source_family_drift}" 'SOURCE_FAMILY = "wazuh_detection"'

backend_publish="${workdir}/backend-publish"
copy_fixture "${backend_publish}"
printf '\n# forbidden host backend publication: "8080:8080"\n' \
  >>"${backend_publish}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with "${backend_publish}" '"8080:8080"'

case_promotion="${workdir}/case-promotion"
copy_fixture "${case_promotion}"
perl -0pi -e \
  's#("case_id": \{\s+"type": )"null"#$1"string"#' \
  "${case_promotion}/control-plane/deployment/phase-67-integration-lab/wazuh/evidence-manifest.schema.json"
assert_fails_with "${case_promotion}" "must prove no automatic case promotion"

negative_delta_drift="${workdir}/negative-delta-drift"
copy_fixture "${negative_delta_drift}"
perl -0pi -e \
  's#("authoritative_alert_delta": \{\s+"const": )0#$1 1#' \
  "${negative_delta_drift}/control-plane/deployment/phase-67-integration-lab/wazuh/evidence-manifest.schema.json"
assert_fails_with \
  "${negative_delta_drift}" \
  "must prove negative tests write no alert state"

runtime_attribution_removed="${workdir}/runtime-attribution-removed"
copy_fixture "${runtime_attribution_removed}"
perl -0pi -e \
  's/\n    "runtime_artifact_digest",//' \
  "${runtime_attribution_removed}/control-plane/deployment/phase-67-integration-lab/wazuh/evidence-manifest.schema.json"
assert_fails_with \
  "${runtime_attribution_removed}" \
  "must require runtime attribution field runtime_artifact_digest"

secret_argv_regression="${workdir}/secret-argv-regression"
copy_fixture "${secret_argv_regression}"
printf '\n# --header "Authorization: Bearer ${shared_secret}"\n' \
  >>"${secret_argv_regression}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${secret_argv_regression}" \
  'Forbidden Phase 67.2 content in control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh: --header "Authorization: Bearer ${shared_secret}"'

runtime_check_removed="${workdir}/runtime-check-removed"
copy_fixture "${runtime_check_removed}"
sed -i.bak \
  's/running Phase 67 artifacts do not match the worktree/runtime artifacts accepted/' \
  "${runtime_check_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${runtime_check_removed}" \
  "running Phase 67 artifacts do not match the worktree"

active_manager_config_check_removed="${workdir}/active-manager-config-check-removed"
copy_fixture "${active_manager_config_check_removed}"
sed -i.bak \
  's#runtime_file_digest wazuh-manager /var/ossec/etc/ossec.conf#runtime_file_digest wazuh-manager /tmp/reviewed-ossec.conf#' \
  "${active_manager_config_check_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${active_manager_config_check_removed}" \
  "runtime_file_digest wazuh-manager /var/ossec/etc/ossec.conf"

authoritative_rule_boundary_removed="${workdir}/authoritative-rule-boundary-removed"
copy_fixture "${authoritative_rule_boundary_removed}"
sed -i.bak \
  's/REVIEWED_WAZUH_DETECTION_RULE_ID = "5710"/REVIEWED_WAZUH_DETECTION_RULE_ID = "5711"/' \
  "${authoritative_rule_boundary_removed}/control-plane/aegisops/control_plane/reviewed_slice_policy.py"
assert_fails_with \
  "${authoritative_rule_boundary_removed}" \
  'REVIEWED_WAZUH_DETECTION_RULE_ID = "5710"'

unreviewed_rule_probe_removed="${workdir}/unreviewed-rule-probe-removed"
copy_fixture "${unreviewed_rule_probe_removed}"
sed -i.bak \
  's/unreviewed Wazuh rule must return HTTP 400/unreviewed Wazuh rule accepted/' \
  "${unreviewed_rule_probe_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${unreviewed_rule_probe_removed}" \
  "unreviewed Wazuh rule must return HTTP 400"

duplicate_event="${workdir}/duplicate-event"
copy_fixture "${duplicate_event}"
sed -i.bak \
  '/Failed password for invalid user aegisops-phase67-invalid/p' \
  "${duplicate_event}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${duplicate_event}" \
  "trial must emit exactly one native rule-5710 event"

manager_recreate_removed="${workdir}/manager-recreate-removed"
copy_fixture "${manager_recreate_removed}"
sed -i.bak \
  's/wazuh-integration-artifacts.sha256/wazuh-integration-artifacts.removed/' \
  "${manager_recreate_removed}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with \
  "${manager_recreate_removed}" \
  "wazuh-integration-artifacts.sha256"

manager_source_binding_removed="${workdir}/manager-source-binding-removed"
copy_fixture "${manager_source_binding_removed}"
sed -i.bak \
  's/cmp -s "${expected_manager_config}" "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"/cmp -s "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}" "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"/' \
  "${manager_source_binding_removed}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with \
  "${manager_source_binding_removed}" \
  'cmp -s "${expected_manager_config}" "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"'

localized_timestamp="${workdir}/localized-timestamp"
copy_fixture "${localized_timestamp}"
sed -i.bak \
  "s/LC_ALL=C date -u/date -u/" \
  "${localized_timestamp}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${localized_timestamp}" \
  "LC_ALL=C date -u '+%b %e %H:%M:%S'"

fixture_timestamp_drift="${workdir}/fixture-timestamp-drift"
copy_fixture "${fixture_timestamp_drift}"
sed -i.bak \
  's/2026-07-27T23:33:37.232+0000/2026-07-27T23:33:37.232/' \
  "${fixture_timestamp_drift}/control-plane/tests/fixtures/wazuh/phase67-real-wazuh-ssh-auth-failure-alert.json"
assert_fails_with \
  "${fixture_timestamp_drift}" \
  '"timestamp": "2026-07-27T23:33:37.232+0000"'

bypass_test_removed="${workdir}/bypass-test-removed"
copy_fixture "${bypass_test_removed}"
sed -i.bak \
  's/direct backend bypass unexpectedly succeeded/direct request allowed/' \
  "${bypass_test_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with "${bypass_test_removed}" "direct backend bypass unexpectedly succeeded"

echo "Phase 67.2 verifier self-test passed."
