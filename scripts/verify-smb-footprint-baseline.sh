#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/smb-footprint-and-deployment-profile-baseline.md"
readme_path="${repo_root}/README.md"
runbook_path="${repo_root}/docs/runbook.md"
roadmap_path="${repo_root}/docs/Revised Phase23-20 Epic Roadmap.md"

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

require_file "${doc_path}" "SMB footprint baseline document"
require_file "${readme_path}" "README"
require_file "${runbook_path}" "runbook document"
require_file "${roadmap_path}" "Phase 23 roadmap document"

required_headings=(
  "# SMB Footprint and Deployment-Profile Baseline"
  "## 1. Purpose"
  "## 2. Scope and Decision Rule"
  "## 3. Reviewed Deployment Profiles"
  "### 3.1 Lab Profile"
  "### 3.2 Consultant-Managed Single-Customer Profile"
  "### 3.3 Small-Production SMB Operation Profile"
  "## 4. Baseline Expectations by Profile"
  "## 5. Operational Burden Baseline"
  "## 6. Alignment to Phase 23 Product Thesis"
  "## 7. Explicitly Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${doc_path}" "${heading}" "SMB footprint baseline heading"
done

required_phrases=(
  "This baseline publishes the reviewed SMB deployment profiles that future footprint, reliability, and operator-experience work must target."
  "Use this baseline to judge whether AegisOps remains operable for the approved small-team deployment target before later work adds substrate, reliability, or ergonomics scope."
  "A profile is acceptable only if it preserves the positive SMB value proposition and remains realistic for a small business-hours SecOps team to operate."
  "The lab profile is the minimum reviewable footprint for first-boot exercises, restore rehearsal, and operator training."
  "The consultant-managed single-customer profile is the default reviewed deployment shape for a small external operator team managing one customer environment."
  "The small-production SMB operation profile is the maximum reviewed baseline for Phase 23 roadmap decisions."
  "| Profile | Managed endpoints | vCPU | Memory | Primary storage | Backup and restore expectation | Operator overhead expectation |"
  "| Lab |"
  "| Consultant-managed single-customer |"
  "| Small-production SMB operation |"
  "CPU and memory expectations must be read as whole-environment planning guidance for the approved control-plane footprint, not as per-container reservations."
  "Backup expectations must include PostgreSQL-aware backups, configuration backup, and a restore rehearsal expectation rather than relying on hypervisor snapshots alone."
  "Operator-overhead expectations are part of the footprint baseline because a deployment that fits on paper but requires enterprise-style staffing is out of scope."
  "The approved small-team operating assumption remains 2 to 6 business-hours SecOps operators with 1 to 3 designated approvers or escalation owners."
  "Phase 23 hardening and ergonomics work must stay inside these reviewed profiles unless a later ADR approves a new target footprint."
  "This baseline supports the product thesis that AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model."
  "High-availability overbuild, large-cluster sizing, and generic enterprise capacity planning are explicitly out of scope for this baseline."
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}" "SMB footprint baseline statement"
done

require_phrase "${readme_path}" "docs/smb-footprint-and-deployment-profile-baseline.md" "README SMB footprint baseline reference"
require_phrase "${runbook_path}" "docs/smb-footprint-and-deployment-profile-baseline.md" "runbook SMB footprint baseline reference"
require_phrase "${roadmap_path}" "docs/smb-footprint-and-deployment-profile-baseline.md" "roadmap SMB footprint baseline reference"

echo "SMB footprint baseline document is present, structured, and linked from the README, runbook, and Phase 23 roadmap."
