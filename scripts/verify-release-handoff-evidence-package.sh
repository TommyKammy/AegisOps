#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/verify-release-handoff-evidence-package.sh [<repo-root>] [--manifest <release-handoff-manifest.md>]

Validates the Phase 38 release handoff evidence package. When a manifest is
supplied, validates that the retained handoff index contains the required
release readiness, preflight, smoke, recovery, limitation, rollback, owner, and
next-review entries without placeholder or workstation-local values.
EOF
}

repo_root=""
manifest_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest)
      if [[ $# -lt 2 ]]; then
        usage
        exit 2
      fi
      manifest_path="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -n "${repo_root}" ]]; then
        usage
        exit 2
      fi
      repo_root="$1"
      shift
      ;;
  esac
done

if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

doc_path="${repo_root}/docs/deployment/release-handoff-evidence-package.md"
template_path="${repo_root}/docs/deployment/release-handoff-evidence-manifest.template.md"
exemplar_path="${repo_root}/docs/deployment/release-handoff-evidence-manifest.single-customer-pilot.example.md"
runbook_path="${repo_root}/docs/runbook.md"
inventory_path="${repo_root}/docs/deployment/single-customer-release-bundle-inventory.md"
smoke_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"
restore_path="${repo_root}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
rehearsal_path="${repo_root}/docs/deployment/customer-like-rehearsal-environment.md"
install_preflight_path="${repo_root}/scripts/verify-single-customer-install-preflight.sh"
smoke_gate_path="${repo_root}/scripts/run-phase-37-runtime-smoke-gate.sh"
restore_verifier_path="${repo_root}/scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_executable() {
  local path="$1"
  local description="$2"

  require_file "${path}" "${description}"
  if [[ ! -x "${path}" ]]; then
    echo "Missing executable bit for ${description}: ${path}" >&2
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

reject_placeholders() {
  local path="$1"
  local description="$2"

  if grep -Eiq 'TODO|sample secret|fake secret|placeholder credential|change-me|replace-with|guess(ed)? scope|unsigned token|<replace-[^>]+>' "${path}"; then
    echo "Placeholder or untrusted ${description} value detected: ${path}" >&2
    exit 1
  fi
}

reject_workstation_paths() {
  local description="$1"
  shift

  local macos_home_pattern linux_home_pattern windows_home_pattern workstation_local_path_pattern
  macos_home_pattern='/'"Users"'/[^[:space:])>]+'
  linux_home_pattern='/'"home"'/[^[:space:])>]+'
  windows_home_pattern='[A-Za-z]:\\'"Users"'\\[^[:space:])>]+'
  workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"

  if grep -Eq "${workstation_local_path_pattern}" "$@"; then
    echo "Forbidden ${description}: workstation-local absolute path detected" >&2
    exit 1
  fi
}

require_file "${doc_path}" "Phase 38 release handoff evidence package"
require_file "${template_path}" "Phase 38 release handoff evidence manifest template"
require_file "${exemplar_path}" "Phase 38 filled redacted release handoff evidence exemplar"
require_file "${runbook_path}" "runbook document"
require_file "${inventory_path}" "single-customer release bundle inventory"
require_file "${smoke_path}" "runtime smoke bundle"
require_file "${restore_path}" "restore rollback upgrade evidence rehearsal"
require_file "${handoff_path}" "operational evidence handoff pack"
require_file "${rehearsal_path}" "customer-like rehearsal environment"
require_executable "${install_preflight_path}" "single-customer install preflight verifier"
require_executable "${smoke_gate_path}" "Phase 37 runtime smoke gate"
require_executable "${restore_verifier_path}" "Phase 37 restore rollback upgrade evidence verifier"

required_headings=(
  "# Phase 38 Release Handoff Evidence Package"
  "## 1. Purpose and Boundary"
  "## 2. Required Handoff Entries"
  "## 3. Evidence Sources"
  "## 4. Blocking Outcomes"
  "## 5. Retention and Path Hygiene"
  "## 6. Verification"
  "## 7. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${doc_path}" "${heading}" "Phase 38 release handoff evidence package heading"
done

required_doc_phrases=(
  "This document defines the Phase 38 release handoff evidence package for a single-customer launch or reviewed upgrade."
  "The package is a bounded repo-owned handoff index, not a new external archive platform, compliance framework, or workflow authority."
  "AegisOps approval, evidence, execution, reconciliation, readiness, and recovery truth remains in the reviewed AegisOps records and release-gate evidence; downstream tickets, substrate receipts, and operator notes are subordinate context only."
  "Every release handoff manifest must include release readiness summary, release bundle identifier, install preflight result, runtime smoke result, backup, restore, rollback, and upgrade rehearsal reference, known limitations, rollback instructions, handoff owner, and next health review."
  "Release notes and known limitations must point to the operator handoff record and the rollback decision record so a launch reviewer can see whether limitations block launch, normal operation, or rollback acceptance."
  'Install preflight evidence comes from `scripts/verify-single-customer-install-preflight.sh --env-file <runtime-env-file>`.'
  'Runtime smoke evidence comes from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`.'
  'Restore, rollback, and upgrade evidence comes from `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>`.'
  "A failed install preflight, runtime smoke, restore validation, rollback rehearsal, upgrade evidence check, or missing known-limitation review blocks launch handoff and normal operation until the failed prerequisite is fixed or the refusal is retained as the handoff outcome."
  "The package keeps the current launch or upgrade handoff, the linked release-gate manifest, the latest runtime smoke manifest, and the next health review expectation; it does not promise unlimited retention."
  'The manifest must use repo-relative paths, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, and `<release-handoff-manifest.md>`.'
  'Verify a retained release handoff manifest with `scripts/verify-release-handoff-evidence-package.sh --manifest <release-handoff-manifest.md>`.'
  "The verifier fails closed when required handoff entries are missing, placeholder-only, sample, guessed, stale, workstation-local, or when required cross-links to Phase 37 smoke, restore, rollback, upgrade, release bundle, runbook, and operational handoff material are missing."
  "External archive platforms, unlimited retention promises, compliance-framework generalization, external ticket lifecycle authority, multi-customer evidence warehouses, direct backend exposure, optional-extension launch gates, and customer-private production access are out of scope."
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}" "Phase 38 release handoff evidence package statement"
done

required_template_phrases=(
  "# Phase 38 Release Handoff Evidence Manifest"
  "Release readiness summary:"
  "Release bundle identifier:"
  "Install preflight result:"
  "Runtime smoke result:"
  "Backup restore rollback upgrade rehearsal:"
  "Known limitations:"
  "Rollback instructions:"
  "Handoff owner:"
  "Next health review:"
  "Authority boundary: AegisOps approval, evidence, execution, reconciliation, readiness, and recovery records remain authoritative; external records are subordinate context only."
)

for phrase in "${required_template_phrases[@]}"; do
  require_phrase "${template_path}" "${phrase}" "Phase 38 release handoff evidence manifest template entry"
done

required_exemplar_phrases=(
  "# Phase 38 Release Handoff Evidence Manifest - Filled Redacted Single-Customer Pilot Example"
  "Release readiness summary:"
  "Release bundle identifier: aegisops-single-customer-pilot-2026-04-27-c4527e5"
  "Install preflight result:"
  "Runtime smoke result:"
  "Backup restore rollback upgrade rehearsal:"
  "Known limitations:"
  "Rollback instructions:"
  "Handoff owner:"
  "Next health review:"
  "Refused or missing evidence handling:"
  "Subordinate context only:"
  "Authority boundary: AegisOps approval, evidence, execution, reconciliation, readiness, and recovery records remain authoritative; external records are subordinate context only."
)

for phrase in "${required_exemplar_phrases[@]}"; do
  require_phrase "${exemplar_path}" "${phrase}" "Phase 38 filled redacted release handoff exemplar entry"
done

reject_placeholders "${exemplar_path}" "Phase 38 filled redacted release handoff exemplar"

require_phrase "${runbook_path}" 'Before launch, upgrade, rollback, restore, or operator handoff closes, assemble the Phase 38 release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` and verify its manifest with `scripts/verify-release-handoff-evidence-package.sh --manifest <release-handoff-manifest.md>`.' "runbook release handoff package link"
require_phrase "${inventory_path}" 'The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` is the Phase 38 handoff index that ties the release bundle identifier, install preflight result, runtime smoke, restore, rollback, upgrade, known limitations, rollback instructions, handoff owner, and next health review to one bounded record.' "release bundle inventory release handoff package link"
require_phrase "${smoke_path}" 'The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` must retain the runtime smoke manifest reference for launch, upgrade, rollback, restore restart, and operator handoff readiness.' "runtime smoke release handoff package link"
require_phrase "${restore_path}" 'The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` consumes the verified restore, rollback, and upgrade release-gate manifest as the authoritative recovery evidence reference for the handoff window.' "restore rollback upgrade release handoff package link"
require_phrase "${handoff_path}" 'For Phase 38 release handoff, use `docs/deployment/release-handoff-evidence-package.md` as the one launch or upgrade handoff index; this operational pack remains retained evidence guidance and does not become workflow authority.' "operational evidence release handoff package link"
require_phrase "${rehearsal_path}" 'The release handoff evidence package in `docs/deployment/release-handoff-evidence-package.md` records the install preflight and customer-like rehearsal result before launch handoff can close.' "customer-like rehearsal release handoff package link"

for forbidden in \
  "requires external archive platform" \
  "requires unlimited retention" \
  "external tickets are authoritative" \
  "requires compliance framework" \
  "requires optional extension" \
  "requires direct backend exposure"; do
  if grep -Fqi -- "${forbidden}" "${doc_path}"; then
    echo "Forbidden Phase 38 release handoff package statement: ${forbidden}" >&2
    exit 1
  fi
done

reject_workstation_paths "Phase 38 release handoff evidence package guidance" \
  "${doc_path}" \
  "${template_path}" \
  "${exemplar_path}" \
  "${runbook_path}" \
  "${inventory_path}" \
  "${smoke_path}" \
  "${restore_path}" \
  "${handoff_path}" \
  "${rehearsal_path}"

if [[ -n "${manifest_path}" ]]; then
  require_file "${manifest_path}" "Phase 38 release handoff evidence manifest"
  reject_placeholders "${manifest_path}" "Phase 38 release handoff manifest"
  reject_workstation_paths "Phase 38 release handoff evidence manifest" "${manifest_path}"

  required_manifest_phrases=(
    "# Phase 38 Release Handoff Evidence Manifest"
    "Release readiness summary:"
    "Release bundle identifier:"
    "Install preflight result:"
    "Runtime smoke result:"
    "Backup restore rollback upgrade rehearsal:"
    "Known limitations:"
    "Rollback instructions:"
    "Handoff owner:"
    "Next health review:"
    "Authority boundary: AegisOps approval, evidence, execution, reconciliation, readiness, and recovery records remain authoritative; external records are subordinate context only."
  )

  for phrase in "${required_manifest_phrases[@]}"; do
    require_phrase "${manifest_path}" "${phrase}" "Phase 38 release handoff manifest entry"
  done
fi

echo "Phase 38 release handoff evidence package is documented, cross-linked, and fail-closed."
