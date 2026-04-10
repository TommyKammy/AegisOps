#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
template_path="${script_dir}/ossec.integration.sample.xml"
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

escape_sed_replacement() {
  printf '%s' "${1}" | sed -e 's/[&|\\]/\\&/g'
}

require_env "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL"
require_env "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE"

if [[ ! -f "${template_path}" ]]; then
  echo "Missing integration template: ${template_path}" >&2
  exit 1
fi

if [[ ! -f "${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE}" ]]; then
  echo "Missing shared secret file: ${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE}" >&2
  exit 1
fi

shared_secret="$(<"${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE}")"
shared_secret="${shared_secret%$'\n'}"
shared_secret="${shared_secret%$'\r'}"
AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET="${shared_secret}"

escaped_ingest_url="$(xml_escape "${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}")"
escaped_shared_secret="$(xml_escape "${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET}")"

mkdir -p "$(dirname "${output_path}")"

sed \
  -e "s|\${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}|$(escape_sed_replacement "${escaped_ingest_url}")|g" \
  -e "s|\${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET}|$(escape_sed_replacement "${escaped_shared_secret}")|g" \
  "${template_path}" >"${output_path}"

echo "Rendered ${output_path}"
