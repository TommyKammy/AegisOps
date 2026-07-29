#!/usr/bin/env bash

set -euo pipefail

install_managed_artifact() {
  local mode="$1"
  local source="$2"
  local destination="$3"

  [[ -s "${source}" ]] || {
    printf 'Required Wazuh runtime artifact is missing or empty: %s\n' "${source}" >&2
    exit 1
  }
  install \
    --owner root \
    --group wazuh \
    --mode "${mode}" \
    "${source}" \
    "${destination}"
}

install_managed_artifact \
  0750 \
  /opt/aegisops-wazuh/custom-aegisops \
  /var/ossec/integrations/custom-aegisops
install_managed_artifact \
  0640 \
  /opt/aegisops-wazuh/aegisops_wazuh_integrator.py \
  /var/ossec/integrations/aegisops_wazuh_integrator.py
install_managed_artifact \
  0644 \
  /run/aegisops-bootstrap/lab.crt \
  /var/ossec/integrations/aegisops-lab-ca.crt
install \
  --directory \
  --owner root \
  --group wazuh \
  --mode 0770 \
  /var/ossec/logs/integrations
install \
  --owner root \
  --group wazuh \
  --mode 0640 \
  /dev/null \
  /var/ossec/logs/aegisops-phase67-ssh-test.log

exec /init "$@"
