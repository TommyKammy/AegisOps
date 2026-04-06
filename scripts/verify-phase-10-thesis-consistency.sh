#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

required_artifacts=(
  "README.md"
  "docs/requirements-baseline.md"
  "docs/architecture.md"
  "docs/secops-domain-model.md"
  "docs/control-plane-state-model.md"
  "docs/repository-structure-baseline.md"
)

check_required_artifacts() {
  local path

  for path in "${required_artifacts[@]}"; do
    if [[ ! -f "${repo_root}/${path}" ]]; then
      echo "Missing Phase 10 thesis artifact: ${path}" >&2
      exit 1
    fi
  done
}

check_marker() {
  local path="$1"
  local marker="$2"

  if ! grep -Fq -- "${marker}" "${repo_root}/${path}"; then
    echo "Missing thesis marker in ${path}: ${marker}" >&2
    exit 1
  fi
}

check_forbidden() {
  local path="$1"
  local marker="$2"

  if grep -Fq -- "${marker}" "${repo_root}/${path}"; then
    echo "Forbidden thesis contradiction in ${path}: ${marker}" >&2
    exit 1
  fi
}

run_reviewed_verifier() {
  local script_name="$1"

  bash "${script_dir}/${script_name}" "${repo_root}"
}

check_required_artifacts

run_reviewed_verifier "verify-requirements-baseline-control-plane-thesis.sh"
run_reviewed_verifier "verify-readme-and-repository-structure-control-plane-thesis.sh"
run_reviewed_verifier "verify-architecture-doc.sh"
run_reviewed_verifier "verify-secops-domain-model-doc.sh"
run_reviewed_verifier "verify-control-plane-state-model-doc.sh"
run_reviewed_verifier "verify-repository-structure-doc.sh"

check_marker "README.md" "AegisOps is built to support **human-controlled security operations** with an explicit authority boundary for approvals, evidence, action intent, and reconciliation."
check_marker "docs/requirements-baseline.md" "OpenSearch, Sigma, and n8n are **not** co-equal product cores for AegisOps."
check_marker "docs/architecture.md" "OpenSearch, Sigma, and n8n may still appear in the repository structure as optional, transitional, or experimental components, but they are no longer the product core in the approved architecture baseline."
check_marker "docs/secops-domain-model.md" "An analytic signal is the common upstream product primitive from which alert or case routing decisions begin."
check_marker "docs/control-plane-state-model.md" "The approved future persistence boundary for those platform-owned control records is an AegisOps-owned PostgreSQL-backed control-plane datastore boundary."
check_marker "docs/repository-structure-baseline.md" "The reviewed top-level tree remains transitional relative to the control-plane thesis until a later ADR explicitly approves a different repository rebaseline."

check_forbidden "README.md" "**AegisOps** is primarily an OpenSearch-and-n8n product core."

echo "Phase 10 thesis artifacts are present and remain aligned to the reviewed control-plane thesis."
