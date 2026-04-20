#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="${repo_root//\\//}"
readme_path="${repo_root}/README.md"
architecture_path="${repo_root}/docs/architecture.md"
roadmap_path="${repo_root}/docs/Revised Phase23-29 Epic Roadmap.md"
requirements_path="${repo_root}/docs/requirements-baseline.md"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

forbid_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if grep -Fq -- "${phrase}" "${path}"; then
    echo "Forbidden ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_file "${readme_path}" "README"
require_file "${architecture_path}" "architecture document"
require_file "${roadmap_path}" "Phase 23 roadmap document"
require_file "${requirements_path}" "requirements baseline document"

positive_thesis="AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model."
target_profile="The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners."
business_hours="The target operating assumption is business-hours review with explicit after-hours escalation, not a 24x7 staffed SOC."

require_phrase "${readme_path}" "${positive_thesis}" "README SMB value proposition statement"
require_phrase "${readme_path}" "${target_profile}" "README deployment target profile"
require_phrase "${readme_path}" "${business_hours}" "README business-hours target statement"

require_phrase "${architecture_path}" "${positive_thesis}" "architecture SMB value proposition statement"
require_phrase "${architecture_path}" "${target_profile}" "architecture deployment target profile"
require_phrase "${architecture_path}" "${business_hours}" "architecture business-hours target statement"

require_phrase "${requirements_path}" "${positive_thesis}" "requirements baseline SMB value proposition statement"
require_phrase "${requirements_path}" "${target_profile}" "requirements baseline deployment target profile"
require_phrase "${requirements_path}" "${business_hours}" "requirements baseline business-hours target statement"

require_phrase "${roadmap_path}" "${positive_thesis}" "roadmap SMB value proposition statement"
require_phrase "${roadmap_path}" "${target_profile}" "roadmap deployment target profile"
require_phrase "${roadmap_path}" "${business_hours}" "roadmap business-hours target statement"
require_phrase "${roadmap_path}" "Phases 23-29 hardening, ergonomics, and bounded-extension work must be evaluated against this deployment target before scope expands." "roadmap Phase 23-29 anchoring statement"

forbid_phrase "${readme_path}" "AegisOps is a generic SIEM replacement for broad enterprise operations." "README contradiction marker"
forbid_phrase "${architecture_path}" "AegisOps is a generic SIEM replacement for broad enterprise operations." "architecture contradiction marker"
forbid_phrase "${requirements_path}" "AegisOps is a generic SIEM replacement for broad enterprise operations." "requirements baseline contradiction marker"
forbid_phrase "${roadmap_path}" "AegisOps is a generic SIEM replacement for broad enterprise operations." "roadmap contradiction marker"
forbid_phrase "${requirements_path}" "Multi-tenant packaging is in scope for this roadmap slice." "requirements baseline out-of-scope contradiction"
forbid_phrase "${roadmap_path}" "Multi-tenant packaging is in scope for this roadmap slice." "roadmap out-of-scope contradiction"

echo "Positive SMB value proposition and deployment target profile are aligned across README, architecture, requirements baseline, and roadmap."
