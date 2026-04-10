#!/usr/bin/env bash

set -euo pipefail

output_path="${1:-./ossec.integration.rendered.xml}"

require_env() {
  local name="$1"

  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
}

xml_escape() {
  local value="$1"

  printf '%s' "${value}" | sed \
    -e 's/&/\&amp;/g' \
    -e 's/</\&lt;/g' \
    -e 's/>/\&gt;/g' \
    -e 's/"/\&quot;/g' \
    -e "s/'/\&apos;/g"
}

require_env "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL"
require_env "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE"

if [[ ! -f "${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE}" ]]; then
  echo "Missing shared secret file: ${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE}" >&2
  exit 1
fi

shared_secret="$(<"${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE}")"
shared_secret="${shared_secret%$'\n'}"
shared_secret="${shared_secret%$'\r'}"

mkdir -p "$(dirname "${output_path}")"

cat >"${output_path}" <<EOF
<!-- Rendered from ossec.integration.sample.xml for reviewed Phase 18 lab use only. -->
<integration>
  <name>aegisops-github-audit</name>
  <hook_url>$(xml_escape "${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}")</hook_url>
  <api_key>$(xml_escape "${shared_secret}")</api_key>
  <alert_format>json</alert_format>
  <level>3</level>
  <group>github_audit</group>
</integration>
EOF

echo "Rendered ${output_path}"
