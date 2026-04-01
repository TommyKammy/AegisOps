#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docs_dir="${repo_root}/docs/parameters"

doc_names=(
  "network-parameters.md"
  "compute-parameters.md"
  "storage-parameters.md"
  "platform-parameters.md"
  "security-parameters.md"
  "operations-parameters.md"
)

required_phrases=(
  "This placeholder document exists to reserve the approved"
  "parameter category for future AegisOps catalog entries."
  "It describes category purpose only."
  "No production values, environment-specific settings, or secrets belong in this file."
)

for doc_name in "${doc_names[@]}"; do
  doc_path="${docs_dir}/${doc_name}"

  if [[ ! -f "${doc_path}" ]]; then
    echo "Missing parameter category document: ${doc_path}" >&2
    exit 1
  fi

  for phrase in "${required_phrases[@]}"; do
    if ! grep -Fq "${phrase}" "${doc_path}"; then
      echo "Missing placeholder statement in ${doc_path}: ${phrase}" >&2
      exit 1
    fi
  done

  if ! grep -Eq '^# AegisOps .+ Parameters$' "${doc_path}"; then
    echo "Missing parameter document title in ${doc_path}" >&2
    exit 1
  fi
done

echo "Parameter category placeholder documents exist and remain descriptive-only."
