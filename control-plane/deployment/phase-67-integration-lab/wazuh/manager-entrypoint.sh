#!/usr/bin/env bash

set -euo pipefail

install \
  --owner root \
  --group wazuh \
  --mode 0750 \
  /opt/aegisops-wazuh/custom-aegisops \
  /var/ossec/integrations/custom-aegisops
install \
  --owner root \
  --group wazuh \
  --mode 0640 \
  /opt/aegisops-wazuh/aegisops_wazuh_integrator.py \
  /var/ossec/integrations/aegisops_wazuh_integrator.py
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
