#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

required_files=(
  "control-plane/README.md"
  "control-plane/main.py"
  "control-plane/aegisops_control_plane/__init__.py"
  "control-plane/aegisops_control_plane/config.py"
  "control-plane/aegisops_control_plane/service.py"
  "control-plane/aegisops_control_plane/adapters/__init__.py"
  "control-plane/aegisops_control_plane/adapters/opensearch.py"
  "control-plane/aegisops_control_plane/adapters/postgres.py"
  "control-plane/aegisops_control_plane/adapters/n8n.py"
  "control-plane/tests/test_runtime_skeleton.py"
  "control-plane/config/local.env.sample"
)

for relative_path in "${required_files[@]}"; do
  full_path="${repo_root}/${relative_path}"
  if [[ ! -f "${full_path}" ]]; then
    echo "Missing control-plane runtime skeleton file: ${relative_path}" >&2
    exit 1
  fi
done

env_sample="${repo_root}/control-plane/config/local.env.sample"
required_env_lines=(
  "AEGISOPS_CONTROL_PLANE_HOST=127.0.0.1"
  "AEGISOPS_CONTROL_PLANE_PORT=8080"
  "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=<set-me>"
  "AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=<set-me>"
  "AEGISOPS_CONTROL_PLANE_N8N_BASE_URL=<set-me>"
)
actual_env_line_count=0

for expected_line in "${required_env_lines[@]}"; do
  if ! grep -Fqx -- "${expected_line}" "${env_sample}"; then
    echo "Missing control-plane local sample setting: ${expected_line}" >&2
    exit 1
  fi
done

while IFS= read -r line; do
  [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue
  actual_env_line_count=$((actual_env_line_count + 1))
  if ! grep -Fqx -- "${line}" <(printf '%s\n' "${required_env_lines[@]}"); then
    echo "Unexpected control-plane local sample setting: ${line}" >&2
    exit 1
  fi
done < "${env_sample}"

if [[ "${actual_env_line_count}" -ne "${#required_env_lines[@]}" ]]; then
  echo "Control-plane local env sample must define exactly ${#required_env_lines[@]} non-comment settings." >&2
  exit 1
fi

if grep -Eq '://[^<[:space:]]+:[^<[:space:]]+@' "${env_sample}"; then
  echo "Control-plane local env sample must not contain embedded credentials." >&2
  exit 1
fi

if ! grep -Fq 'AegisOpsControlPlaneService' "${repo_root}/control-plane/aegisops_control_plane/service.py"; then
  echo "Control-plane service module must define AegisOpsControlPlaneService." >&2
  exit 1
fi

if ! grep -Fq 'build_runtime_snapshot' "${repo_root}/control-plane/main.py"; then
  echo "Control-plane entrypoint must build a runtime snapshot." >&2
  exit 1
fi

echo "Control-plane runtime skeleton is present, separated, and configured with non-secret local placeholders."
