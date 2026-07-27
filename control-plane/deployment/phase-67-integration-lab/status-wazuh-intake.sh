#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_environment
require_command jq

running_services="$(compose_scope wazuh ps --services --status running)"
for required_service in control-plane proxy wazuh-manager; do
  grep -Fqx "${required_service}" <<<"${running_services}" \
    || fail "${required_service} is not running; run ${LAB_DIR}/up.sh wazuh"
done

manager_status="$(
  compose_scope wazuh exec -T wazuh-manager \
    /var/ossec/bin/wazuh-control status || true
)"
printf '%s\n' "${manager_status}"
grep -Fq "wazuh-analysisd is running" <<<"${manager_status}" \
  || fail "Wazuh analysisd is not healthy"
grep -Fq "wazuh-integratord is running" <<<"${manager_status}" \
  || fail "Wazuh integratord is not healthy"

receipt="$(
  compose_scope wazuh exec -T wazuh-manager \
    sh -c '
      receipt=/var/ossec/logs/integrations/aegisops-receipts.jsonl
      if [ -s "${receipt}" ]; then
        tail -n 1 "${receipt}"
      else
        printf "{}\n"
      fi
    '
)"
if [[ "${receipt}" == "{}" ]]; then
  echo "latest_receipt=none"
  exit 0
fi

jq -e '
  {
    native_wazuh_alert_id,
    http_status,
    disposition,
    aegisops_alert_id,
    finding_id,
    reconciliation_id
  }
' <<<"${receipt}"

alert_id="$(jq -er '.aegisops_alert_id' <<<"${receipt}")"
queue="$(
  compose_scope wazuh exec -T control-plane \
    python3 main.py inspect-analyst-queue
)"
jq -e --arg alert_id "${alert_id}" '
  .records[]
  | select(.alert_id == $alert_id)
  | {
      alert_id,
      case_id,
      source_system,
      queue_selection,
      review_state
    }
' <<<"${queue}"
