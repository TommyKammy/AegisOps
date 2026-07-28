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

source_family_attestation_removed="${workdir}/source-family-attestation-removed"
copy_fixture "${source_family_attestation_removed}"
sed -i.bak \
  '/proxy_set_header X-AegisOps-Source-Family "wazuh_detection";/d' \
  "${source_family_attestation_removed}/control-plane/deployment/phase-67-integration-lab/init.sh"
assert_fails_with \
  "${source_family_attestation_removed}" \
  'proxy_set_header X-AegisOps-Source-Family "wazuh_detection";'

source_family_gate_removed="${workdir}/source-family-gate-removed"
copy_fixture "${source_family_gate_removed}"
sed -i.bak \
  's/source_family != attested_source_family/source_family == attested_source_family/' \
  "${source_family_gate_removed}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py"
assert_fails_with \
  "${source_family_gate_removed}" \
  "source_family != attested_source_family"

source_family_requirement_removed="${workdir}/source-family-requirement-removed"
copy_fixture "${source_family_requirement_removed}"
sed -i.bak \
  's/attested_source_family is None/attested_source_family is not None/' \
  "${source_family_requirement_removed}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py"
assert_fails_with \
  "${source_family_requirement_removed}" \
  "attested_source_family is None"

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

shared_alert_identity_removed="${workdir}/shared-alert-identity-removed"
copy_fixture "${shared_alert_identity_removed}"
perl -0pi -e \
  's/\n    "aegisops_alert_id",//' \
  "${shared_alert_identity_removed}/control-plane/deployment/phase-67-integration-lab/wazuh/evidence-manifest.schema.json"
assert_fails_with \
  "${shared_alert_identity_removed}" \
  "must represent one shared AegisOps alert identity"

first_delivery_drift="${workdir}/first-delivery-drift"
copy_fixture "${first_delivery_drift}"
sed -i.bak \
  's/"const": "created"/"const": "deduplicated"/' \
  "${first_delivery_drift}/control-plane/deployment/phase-67-integration-lab/wazuh/evidence-manifest.schema.json"
assert_fails_with \
  "${first_delivery_drift}" \
  "first_delivery must require created"

duplicate_delivery_drift="${workdir}/duplicate-delivery-drift"
copy_fixture "${duplicate_delivery_drift}"
sed -i.bak \
  's/"const": "deduplicated"/"const": "created"/' \
  "${duplicate_delivery_drift}/control-plane/deployment/phase-67-integration-lab/wazuh/evidence-manifest.schema.json"
assert_fails_with \
  "${duplicate_delivery_drift}" \
  "duplicate_delivery must require deduplicated"

divergent_delivery_identity="${workdir}/divergent-delivery-identity"
copy_fixture "${divergent_delivery_identity}"
python3 - \
  "${divergent_delivery_identity}/control-plane/deployment/phase-67-integration-lab/wazuh/evidence-manifest.schema.json" <<'PY'
from pathlib import Path
import json
import sys

path = Path(sys.argv[1])
schema = json.loads(path.read_text(encoding="utf-8"))
definition = schema["$defs"]["duplicate_delivery"]
definition["required"].append("aegisops_alert_id")
definition["properties"]["aegisops_alert_id"] = {
    "type": "string",
    "minLength": 1,
}
path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
PY
assert_fails_with \
  "${divergent_delivery_identity}" \
  "delivery evidence must use the shared aegisops_alert_id"

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

atomic_manifest_publish_removed="${workdir}/atomic-manifest-publish-removed"
copy_fixture "${atomic_manifest_publish_removed}"
sed -i.bak \
  's/mv "${evidence_staging_file}" "${evidence_file}"/cp "${evidence_staging_file}" "${evidence_file}"/' \
  "${atomic_manifest_publish_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${atomic_manifest_publish_removed}" \
  'mv "${evidence_staging_file}" "${evidence_file}"'

schema_validation_removed="${workdir}/schema-validation-removed"
copy_fixture "${schema_validation_removed}"
sed -i.bak \
  '/"${evidence_validator}"/d' \
  "${schema_validation_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${schema_validation_removed}" \
  '"${evidence_validator}"'

manifest_staging_cleanup_removed="${workdir}/manifest-staging-cleanup-removed"
copy_fixture "${manifest_staging_cleanup_removed}"
sed -i.bak \
  's/rm -f "${evidence_staging_file}"/true/' \
  "${manifest_staging_cleanup_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${manifest_staging_cleanup_removed}" \
  'rm -f "${evidence_staging_file}"'

unmanaged_proxy_ca="${workdir}/unmanaged-proxy-ca"
copy_fixture "${unmanaged_proxy_ca}"
sed -i.bak \
  's#/var/ossec/integrations/aegisops-lab-ca.crt#/run/aegisops-bootstrap/lab.crt#' \
  "${unmanaged_proxy_ca}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with \
  "${unmanaged_proxy_ca}" \
  "AEGISOPS_WAZUH_INGEST_CA_FILE: /var/ossec/integrations/aegisops-lab-ca.crt"

proxy_ca_install_removed="${workdir}/proxy-ca-install-removed"
copy_fixture "${proxy_ca_install_removed}"
sed -i.bak \
  's#/var/ossec/integrations/aegisops-lab-ca.crt#/tmp/aegisops-lab-ca.crt#' \
  "${proxy_ca_install_removed}/control-plane/deployment/phase-67-integration-lab/wazuh/manager-entrypoint.sh"
assert_fails_with \
  "${proxy_ca_install_removed}" \
  "/var/ossec/integrations/aegisops-lab-ca.crt"

proxy_ca_recreate_binding_removed="${workdir}/proxy-ca-recreate-binding-removed"
copy_fixture "${proxy_ca_recreate_binding_removed}"
sed -i.bak \
  "s/printf '\\\\0proxy-ca.crt\\\\0'/printf '\\\\0proxy-ca-removed\\\\0'/" \
  "${proxy_ca_recreate_binding_removed}/control-plane/deployment/phase-67-integration-lab/up.sh"
assert_fails_with \
  "${proxy_ca_recreate_binding_removed}" \
  "printf '\\0proxy-ca.crt\\0'"

receipt_lock_removed="${workdir}/receipt-lock-removed"
copy_fixture "${receipt_lock_removed}"
sed -i.bak \
  's/fcntl.flock(descriptor, fcntl.LOCK_EX)/pass/' \
  "${receipt_lock_removed}/control-plane/deployment/phase-67-integration-lab/wazuh/aegisops_wazuh_integrator.py"
assert_fails_with \
  "${receipt_lock_removed}" \
  "fcntl.flock(descriptor, fcntl.LOCK_EX)"

receipt_complete_write_removed="${workdir}/receipt-complete-write-removed"
copy_fixture "${receipt_complete_write_removed}"
sed -i.bak \
  's/_write_all(descriptor, encoded)/os.write(descriptor, encoded)/' \
  "${receipt_complete_write_removed}/control-plane/deployment/phase-67-integration-lab/wazuh/aegisops_wazuh_integrator.py"
assert_fails_with \
  "${receipt_complete_write_removed}" \
  "_write_all(descriptor, encoded)"

receipt_sync_removed="${workdir}/receipt-sync-removed"
copy_fixture "${receipt_sync_removed}"
sed -i.bak \
  's/os.fsync(descriptor)/pass/' \
  "${receipt_sync_removed}/control-plane/deployment/phase-67-integration-lab/wazuh/aegisops_wazuh_integrator.py"
assert_fails_with \
  "${receipt_sync_removed}" \
  "os.fsync(descriptor)"

receipt_rollback_removed="${workdir}/receipt-rollback-removed"
copy_fixture "${receipt_rollback_removed}"
sed -i.bak \
  's/os.ftruncate(descriptor, initial_size)/pass/' \
  "${receipt_rollback_removed}/control-plane/deployment/phase-67-integration-lab/wazuh/aegisops_wazuh_integrator.py"
assert_fails_with \
  "${receipt_rollback_removed}" \
  "os.ftruncate(descriptor, initial_size)"

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

native_provenance_boundary_removed="${workdir}/native-provenance-boundary-removed"
copy_fixture "${native_provenance_boundary_removed}"
sed -i.bak \
  's/if actual_value != expected_value:/if False:/' \
  "${native_provenance_boundary_removed}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py"
assert_fails_with \
  "${native_provenance_boundary_removed}" \
  "if actual_value != expected_value:"

fixed_provenance_boundary_removed="${workdir}/fixed-provenance-boundary-removed"
copy_fixture "${fixed_provenance_boundary_removed}"
sed -i.bak \
  's/REVIEWED_WAZUH_DETECTION_FIXED_PROVENANCE/REMOVED_WAZUH_DETECTION_FIXED_PROVENANCE/g' \
  "${fixed_provenance_boundary_removed}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py"
assert_fails_with \
  "${fixed_provenance_boundary_removed}" \
  "REVIEWED_WAZUH_DETECTION_FIXED_PROVENANCE"

unreviewed_rule_probe_removed="${workdir}/unreviewed-rule-probe-removed"
copy_fixture "${unreviewed_rule_probe_removed}"
sed -i.bak \
  's/unreviewed Wazuh rule must return HTTP 400/unreviewed Wazuh rule accepted/' \
  "${unreviewed_rule_probe_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${unreviewed_rule_probe_removed}" \
  "unreviewed Wazuh rule must return HTTP 400"

fixed_provenance_probe_removed="${workdir}/fixed-provenance-probe-removed"
copy_fixture "${fixed_provenance_probe_removed}"
sed -i.bak \
  's/forged fixed Wazuh provenance must return HTTP 400/forged fixed Wazuh provenance accepted/' \
  "${fixed_provenance_probe_removed}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${fixed_provenance_probe_removed}" \
  "forged fixed Wazuh provenance must return HTTP 400"

duplicate_event="${workdir}/duplicate-event"
copy_fixture "${duplicate_event}"
sed -i.bak \
  '/Failed password for invalid user %s/p' \
  "${duplicate_event}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${duplicate_event}" \
  "trial must emit exactly one native rule-5710 event"

fixed_correlation_identity="${workdir}/fixed-correlation-identity"
copy_fixture "${fixed_correlation_identity}"
sed -i.bak \
  's/trial_username="aegisops-phase67-${trial_nonce}"/trial_username="aegisops-phase67-invalid"/' \
  "${fixed_correlation_identity}/control-plane/deployment/phase-67-integration-lab/test-wazuh-intake.sh"
assert_fails_with \
  "${fixed_correlation_identity}" \
  "must not reuse a fixed correlation identity"

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
