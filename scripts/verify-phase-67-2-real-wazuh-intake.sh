#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
lab_dir="${repo_root}/control-plane/deployment/phase-67-integration-lab"
relative_lab="control-plane/deployment/phase-67-integration-lab"
live_fixture="${repo_root}/control-plane/tests/fixtures/wazuh/phase67-real-wazuh-ssh-auth-failure-alert.json"

fail() {
  echo "$*" >&2
  exit 1
}

require_file() {
  [[ -f "$1" ]] || fail "Missing Phase 67.2 artifact: ${1#${repo_root}/}"
}

require_executable() {
  [[ -x "$1" ]] \
    || fail "Phase 67.2 command must be executable: ${1#${repo_root}/}"
}

require_fixed_string() {
  local path="$1"
  local expected="$2"

  grep -F -- "${expected}" "${path}" >/dev/null \
    || fail "Missing Phase 67.2 contract in ${path#${repo_root}/}: ${expected}"
}

require_absent_string() {
  local path="$1"
  local forbidden="$2"

  if grep -F -- "${forbidden}" "${path}" >/dev/null; then
    fail "Forbidden Phase 67.2 content in ${path#${repo_root}/}: ${forbidden}"
  fi
}

files=(
  config/control-plane.conf
  docker-compose.yml
  init.sh
  prepare-substrates.sh
  up.sh
  test-wazuh-intake.sh
  status-wazuh-intake.sh
  README.md
  RUNBOOK.md
  wazuh/custom-aegisops
  wazuh/aegisops_wazuh_integrator.py
  wazuh/manager-entrypoint.sh
  wazuh/ossec-integration.xml
  wazuh/integrator.env.sample
  wazuh/MAPPING.md
  wazuh/evidence-manifest.schema.json
)
for file in "${files[@]}"; do
  require_file "${lab_dir}/${file}"
done

require_file \
  "${repo_root}/control-plane/tests/test_phase67_2_real_wazuh_intake.py"
require_file "${live_fixture}"
require_file \
  "${repo_root}/control-plane/aegisops/control_plane/reviewed_slice_policy.py"
require_file \
  "${repo_root}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py"
reviewed_slice_policy="${repo_root}/control-plane/aegisops/control_plane/reviewed_slice_policy.py"
intake_helpers="${repo_root}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py"
require_file "${repo_root}/.github/workflows/ci.yml"

for command in \
  test-wazuh-intake.sh \
  status-wazuh-intake.sh \
  wazuh/custom-aegisops \
  wazuh/manager-entrypoint.sh
do
  require_executable "${lab_dir}/${command}"
done

proxy="${lab_dir}/config/control-plane.conf"
compose="${lab_dir}/docker-compose.yml"
init="${lab_dir}/init.sh"
prepare="${lab_dir}/prepare-substrates.sh"
up="${lab_dir}/up.sh"
trial="${lab_dir}/test-wazuh-intake.sh"
status="${lab_dir}/status-wazuh-intake.sh"
integrator="${lab_dir}/wazuh/aegisops_wazuh_integrator.py"
wrapper="${lab_dir}/wazuh/custom-aegisops"
manager_entrypoint="${lab_dir}/wazuh/manager-entrypoint.sh"
integration="${lab_dir}/wazuh/ossec-integration.xml"
env_sample="${lab_dir}/wazuh/integrator.env.sample"
mapping="${lab_dir}/wazuh/MAPPING.md"
schema="${lab_dir}/wazuh/evidence-manifest.schema.json"
policy="${repo_root}/control-plane/aegisops/control_plane/reviewed_slice_policy.py"
ingest_helper="${repo_root}/control-plane/aegisops/control_plane/ingestion/detection_lifecycle_helpers.py"
unit_test="${repo_root}/control-plane/tests/test_phase67_2_real_wazuh_intake.py"
workflow="${repo_root}/.github/workflows/ci.yml"

require_fixed_string "${proxy}" "location = /intake/wazuh {"
require_fixed_string "${proxy}" "limit_except POST {"
require_fixed_string "${proxy}" "client_max_body_size 256k;"
require_fixed_string \
  "${proxy}" \
  "include /etc/nginx/certs/wazuh-intake-auth.conf;"
require_fixed_string \
  "${proxy}" \
  "proxy_pass http://phase67_control_plane/intake/wazuh;"

require_fixed_string \
  "${init}" \
  'proxy_set_header X-Forwarded-For \$remote_addr;'
require_fixed_string \
  "${init}" \
  'proxy_set_header X-Forwarded-Proto https;'
require_fixed_string \
  "${init}" \
  'proxy_set_header X-AegisOps-Proxy-Secret "${wazuh_ingest_proxy_secret}";'
require_fixed_string \
  "${init}" \
  'proxy_set_header X-AegisOps-Authenticated-Role "";'
require_fixed_string "${init}" "DNS:proxy"
require_fixed_string \
  "${init}" \
  "AEGISOPS_LAB_WAZUH_MANAGER_CONFIG"

require_fixed_string \
  "${compose}" \
  "AEGISOPS_WAZUH_INGEST_URL: https://proxy:8443/intake/wazuh"
require_fixed_string \
  "${compose}" \
  "AEGISOPS_WAZUH_INGEST_SHARED_SECRET_FILE: /run/secrets/wazuh-ingest-shared-secret"
require_fixed_string \
  "${compose}" \
  "AEGISOPS_WAZUH_INGEST_CA_FILE: /var/ossec/integrations/aegisops-lab-ca.crt"
require_fixed_string \
  "${compose}" \
  '- ${AEGISOPS_LAB_PROXY_CERT_DIR:?run-init-first}/lab.crt:/run/aegisops-bootstrap/lab.crt:ro'
require_fixed_string \
  "${compose}" \
  'AEGISOPS_WAZUH_ALLOWED_RULE_ID: "5710"'
require_fixed_string \
  "${compose}" \
  "- \${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG:?prepare-substrates-first}:/wazuh-config-mount/etc/ossec.conf:ro"
require_fixed_string \
  "${compose}" \
  "- ./wazuh:/opt/aegisops-wazuh:ro"
require_fixed_string "${compose}" "- wazuh-ingest-shared-secret"
require_absent_string "${compose}" '"8080:8080"'
require_fixed_string \
  "${manager_entrypoint}" \
  "/run/aegisops-bootstrap/lab.crt"
require_fixed_string \
  "${manager_entrypoint}" \
  "/var/ossec/integrations/aegisops-lab-ca.crt"
require_fixed_string "${manager_entrypoint}" "  0644 \\"
require_fixed_string "${integrator}" "fcntl.flock(descriptor, fcntl.LOCK_EX)"
require_fixed_string "${integrator}" "_write_all(descriptor, encoded)"
require_fixed_string "${integrator}" "os.fsync(descriptor)"
require_fixed_string "${integrator}" "os.ftruncate(descriptor, initial_size)"

require_fixed_string \
  "${prepare}" \
  'manager_config_fragment="${LAB_DIR}/wazuh/ossec-integration.xml"'
require_fixed_string \
  "${prepare}" \
  '"${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-manager-config.sha256"'
require_fixed_string \
  "${up}" \
  '"${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-manager-config.sha256"'

require_fixed_string "${integration}" "<name>custom-aegisops</name>"
require_fixed_string \
  "${integration}" \
  "<hook_url>https://proxy:8443/intake/wazuh</hook_url>"
require_fixed_string "${integration}" "<api_key>file-bound</api_key>"
require_fixed_string "${integration}" "<alert_format>json</alert_format>"
require_fixed_string "${integration}" "<rule_id>5710</rule_id>"
require_absent_string "${integration}" "Bearer "

require_fixed_string \
  "${manager_entrypoint}" \
  "--group wazuh"
require_fixed_string \
  "${manager_entrypoint}" \
  "  0750 \\"
require_fixed_string \
  "${manager_entrypoint}" \
  "/var/ossec/integrations/custom-aegisops"
require_fixed_string \
  "${manager_entrypoint}" \
  "/var/ossec/logs/aegisops-phase67-ssh-test.log"
require_fixed_string "${manager_entrypoint}" 'exec /init "$@"'
require_fixed_string "${wrapper}" "from aegisops_wazuh_integrator import main"

require_fixed_string "${integrator}" 'SOURCE_FAMILY = "wazuh_detection"'
require_fixed_string \
  "${integrator}" \
  '"AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE"'
require_fixed_string "${integrator}" '"event_id": native_id'
require_fixed_string "${integrator}" 'parsed.scheme != "https"'
require_fixed_string "${integrator}" 'parsed.path != "/intake/wazuh"'
require_fixed_string "${integrator}" "MAX_ALERT_BYTES = 256 * 1024"
require_fixed_string "${integrator}" "os.O_NOFOLLOW"
require_fixed_string "${integrator}" 'if argv[2] != "file-bound":'
require_absent_string "${integrator}" "fixture-shared-secret"
require_fixed_string \
  "${reviewed_slice_policy}" \
  'REVIEWED_WAZUH_DETECTION_RULE_ID = "5710"'
require_fixed_string \
  "${reviewed_slice_policy}" \
  "REVIEWED_WAZUH_DETECTION_FIXED_PROVENANCE"
require_fixed_string \
  "${intake_helpers}" \
  'native_rule_id != REVIEWED_WAZUH_DETECTION_RULE_ID'
require_fixed_string \
  "${intake_helpers}" \
  'or provenance_rule_id != native_rule_id'
require_fixed_string \
  "${intake_helpers}" \
  'expected_wazuh_provenance.update('
require_fixed_string \
  "${intake_helpers}" \
  'REVIEWED_WAZUH_DETECTION_FIXED_PROVENANCE'
require_fixed_string \
  "${intake_helpers}" \
  'for field_name, expected_value in expected_wazuh_provenance.items():'
require_fixed_string \
  "${intake_helpers}" \
  'if actual_value != expected_value:'

require_fixed_string \
  "${env_sample}" \
  "AEGISOPS_WAZUH_INGEST_SHARED_SECRET_FILE=/run/secrets/wazuh-ingest-shared-secret"
require_fixed_string \
  "${env_sample}" \
  "AEGISOPS_WAZUH_INGEST_CA_FILE=/var/ossec/integrations/aegisops-lab-ca.crt"
require_absent_string "${env_sample}" "AEGISOPS_WAZUH_INGEST_SHARED_SECRET="
require_fixed_string "${mapping}" 'Native Wazuh alert `id`; never generated'
require_fixed_string "${mapping}" "Wazuh remains subordinate detection evidence"
require_fixed_string "${live_fixture}" '"timestamp": "2026-07-27T23:33:37.232+0000"'
require_fixed_string "${live_fixture}" '"id": "1785195217.5695"'
require_fixed_string "${live_fixture}" '"id": "5710"'
require_fixed_string "${live_fixture}" '"srcip": "192.0.2.67"'
require_absent_string "${live_fixture}" "Bearer "
require_absent_string "${live_fixture}" "shared_secret"
python3 -m json.tool "${live_fixture}" >/dev/null

python3 - "${schema}" "${integration}" "${live_fixture}" <<'PY'
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

schema = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if schema["properties"]["source_mode"].get("const") != "real_wazuh":
    raise SystemExit("Phase 67.2 evidence source_mode must be real_wazuh")
if "live_capture_sanitized" not in schema["properties"]["fixture_provenance"].get(
    "enum", []
):
    raise SystemExit("Phase 67.2 evidence must distinguish sanitized live capture")
if schema["properties"]["analyst_queue"]["properties"]["case_id"].get("type") != "null":
    raise SystemExit("Phase 67.2 evidence must prove no automatic case promotion")
if (
    schema["properties"]["negative_boundary"]["properties"][
        "authoritative_alert_delta"
    ].get("const")
    != 0
):
    raise SystemExit("Phase 67.2 evidence must prove negative tests write no alert state")
required = set(schema.get("required", []))
if "aegisops_alert_id" not in required:
    raise SystemExit(
        "Phase 67.2 evidence must represent one shared AegisOps alert identity"
    )
for delivery_name, expected_disposition in (
    ("first_delivery", "created"),
    ("duplicate_delivery", "deduplicated"),
):
    definition = schema["$defs"][delivery_name]
    disposition = definition["properties"]["disposition"].get("const")
    if disposition != expected_disposition:
        raise SystemExit(
            f"Phase 67.2 evidence {delivery_name} must require "
            f"{expected_disposition}"
        )
    if "aegisops_alert_id" in definition["properties"]:
        raise SystemExit(
            "Phase 67.2 delivery evidence must use the shared "
            "aegisops_alert_id"
        )
if "alert_id" in schema["properties"]["analyst_queue"]["properties"]:
    raise SystemExit(
        "Phase 67.2 analyst queue evidence must use the shared "
        "aegisops_alert_id"
    )
for digest_field in ("worktree_artifact_digest", "runtime_artifact_digest"):
    if digest_field not in required:
        raise SystemExit(
            f"Phase 67.2 evidence must require runtime attribution field {digest_field}"
        )
    if schema["properties"][digest_field].get("pattern") != "^[0-9a-f]{64}$":
        raise SystemExit(
            f"Phase 67.2 evidence must constrain {digest_field} to SHA-256"
        )
ET.parse(sys.argv[2])
live_fixture = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
timestamp_pattern = schema["properties"]["native_event_timestamp"].get("pattern", "")
if not re.fullmatch(timestamp_pattern, live_fixture.get("timestamp", "")):
    raise SystemExit("Phase 67.2 live fixture timestamp must satisfy evidence schema")
PY

require_fixed_string "${trial}" "missing Bearer secret must return HTTP 403"
require_fixed_string "${trial}" "invalid Bearer secret must return HTTP 403"
require_fixed_string "${trial}" "malformed JSON must return HTTP 400"
require_fixed_string "${trial}" "unsupported source family must return HTTP 400"
require_fixed_string "${trial}" "unreviewed Wazuh rule must return HTTP 400"
require_fixed_string \
  "${trial}" \
  "forged fixed Wazuh provenance must return HTTP 400"
require_fixed_string "${trial}" "integrator.map_native_alert("
require_fixed_string "${trial}" "oversized payload must return HTTP 413"
require_fixed_string "${trial}" "direct backend bypass unexpectedly succeeded"
require_fixed_string "${trial}" "negative_authoritative_alert_delta=0"
require_fixed_string "${trial}" 'and .disposition == "deduplicated"'
require_fixed_string "${trial}" '.case_id == null'
require_fixed_string "${trial}" 'source_mode: "real_wazuh"'
require_fixed_string "${trial}" 'aegisops_alert_id: $aegisops_alert_id'
require_fixed_string "${trial}" '--header "@${authenticated_header_file}"'
require_absent_string "${trial}" '--header "Authorization: Bearer ${shared_secret}"'
require_absent_string "${trial}" 'tail -n 1 "${receipt_file}"'
require_fixed_string \
  "${trial}" \
  "single trial event produced an unexpected number of Wazuh receipts"
require_fixed_string \
  "${trial}" \
  "running Phase 67 artifacts do not match the worktree"
require_fixed_string \
  "${trial}" \
  '[[ "${runtime_artifact_digest}" == "${worktree_artifact_digest}" ]]'
require_fixed_string \
  "${trial}" \
  'file_digest "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"'
require_fixed_string \
  "${trial}" \
  "runtime_file_digest wazuh-manager /var/ossec/etc/ossec.conf"
require_fixed_string \
  "${trial}" \
  '"wazuh-manager-config=${worktree_manager_config}"'
require_fixed_string \
  "${trial}" \
  '"wazuh-manager-config=${runtime_manager_config}"'
require_fixed_string \
  "${trial}" \
  '"wazuh-proxy-ca=${worktree_proxy_ca}"'
require_fixed_string \
  "${trial}" \
  '"wazuh-proxy-ca=${runtime_proxy_ca}"'
require_fixed_string "${trial}" 'duplicate_receipt_index=$((initial_receipt_count + 2))'
require_fixed_string "${trial}" 'runtime_artifact_digest: $runtime_artifact_digest'
require_fixed_string "${trial}" "LC_ALL=C date -u '+%b %e %H:%M:%S'"
require_fixed_string "${up}" "wazuh-integration-artifacts.sha256"
require_fixed_string "${up}" "printf 'manager-entrypoint.sh\\0'"
require_fixed_string "${up}" "printf '\\0custom-aegisops\\0'"
require_fixed_string "${up}" "printf '\\0aegisops_wazuh_integrator.py\\0'"
require_fixed_string "${up}" "printf '\\0ossec-integration.xml\\0'"
require_fixed_string "${up}" "printf '\\0proxy-ca.crt\\0'"
require_fixed_string \
  "${up}" \
  'cat "${AEGISOPS_LAB_PROXY_CERT_DIR}/lab.crt"'
require_fixed_string \
  "${up}" \
  '[[ "$(<"${wazuh_integration_state}")" != "${wazuh_integration_digest}" ]]'
require_fixed_string \
  "${up}" \
  'cmp -s "${expected_manager_config}" "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"'
require_fixed_string \
  "${up}" \
  "Wazuh manager config does not match its reviewed source fragment"
python3 - "${trial}" <<'PY'
from pathlib import Path
import sys

trial = Path(sys.argv[1]).read_text(encoding="utf-8")
event = "Failed password for invalid user %s"
if trial.count(event) != 1:
    raise SystemExit("Phase 67.2 trial must emit exactly one native rule-5710 event")
if "aegisops-phase67-invalid" in trial:
    raise SystemExit("Phase 67.2 trial must not reuse a fixed correlation identity")
if "secrets.token_hex(8)" not in trial:
    raise SystemExit("Phase 67.2 trial must generate a fresh correlation identity")
if 'trial_username="aegisops-phase67-${trial_nonce}"' not in trial:
    raise SystemExit("Phase 67.2 trial must bind its fresh correlation identity")
PY
require_fixed_string "${status}" "latest_receipt=none"
require_fixed_string "${status}" "inspect-analyst-queue"

require_fixed_string "${policy}" '"wazuh_detection"'
require_fixed_string \
  "${ingest_helper}" \
  "and wazuh_detection live source families"
require_fixed_string \
  "${unit_test}" \
  "test_control_plane_admits_and_deduplicates_native_wazuh_detection"
require_fixed_string \
  "${workflow}" \
  "bash scripts/verify-phase-67-2-real-wazuh-intake.sh"
require_fixed_string \
  "${workflow}" \
  "bash scripts/test-verify-phase-67-2-real-wazuh-intake.sh"

for shell_file in \
  "${lab_dir}"/*.sh \
  "${lab_dir}/wazuh/manager-entrypoint.sh"
do
  bash -n "${shell_file}"
done
python3 -m py_compile "${integrator}" "${wrapper}"

if [[
  -f "${repo_root}/control-plane/aegisops/control_plane/service.py" &&
    -f "${unit_test}"
]]; then
  (
    cd "${repo_root}"
    python3 -m unittest control-plane.tests.test_phase67_2_real_wazuh_intake
  )
fi

echo "Phase 67.2 real Wazuh intake verification passed."
echo "lab=${relative_lab}"
