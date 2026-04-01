#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config_dir="${repo_root}/config/parameters"

required_files=(
  "network.yaml"
  "compute.yaml"
  "storage.yaml"
  "platform.yaml"
  "security.yaml"
  "operations.yaml"
)

required_phrases=(
  "schema_version: 1"
  "status: placeholder"
  "non_secret: true"
  "environment: template"
  "values: {}"
)

if [[ ! -d "${config_dir}" ]]; then
  echo "Missing config parameters directory: ${config_dir}" >&2
  exit 1
fi

for file_name in "${required_files[@]}"; do
  file_path="${config_dir}/${file_name}"
  category="${file_name%.yaml}"

  if [[ ! -f "${file_path}" ]]; then
    echo "Missing parameter config file: ${file_path}" >&2
    exit 1
  fi

  if ! grep -Fxq "category: ${category}" "${file_path}"; then
    echo "Missing category marker in ${file_path}" >&2
    exit 1
  fi

  for phrase in "${required_phrases[@]}"; do
    if ! grep -Fq "${phrase}" "${file_path}"; then
      echo "Missing placeholder field in ${file_path}: ${phrase}" >&2
      exit 1
    fi
  done

  if grep -Eiq '(^|[^[:alnum:]_])(password|secret|token|private_key|api_key)([^[:alnum:]_]|$)|BEGIN [A-Z ]+PRIVATE KEY' "${file_path}"; then
    echo "Potential secret material detected in ${file_path}" >&2
    exit 1
  fi
done

echo "Machine-readable parameter placeholder files exist and remain non-secret."
