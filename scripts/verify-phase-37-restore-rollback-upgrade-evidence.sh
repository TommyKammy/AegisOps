#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh [<repo-root>] [--manifest <release-gate-manifest.md>]

Validates the Phase 37 restore, rollback, upgrade, smoke, and handoff evidence
rehearsal contract. When a manifest is supplied, validates that the retained
manifest ties the required evidence together and fails closed on missing or
placeholder entries.
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

doc_path="${repo_root}/docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md"
runbook_path="${repo_root}/docs/runbook.md"
rehearsal_path="${repo_root}/docs/deployment/customer-like-rehearsal-environment.md"
smoke_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"
handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
record_chain_path="${repo_root}/scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh"
smoke_gate_path="${repo_root}/scripts/run-phase-37-runtime-smoke-gate.sh"

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

  if grep -Eiq 'TODO|sample secret|fake secret|placeholder credential|change-me|guess(ed)? scope|unsigned token' "${path}"; then
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

require_file "${doc_path}" "Phase 37 restore rollback upgrade evidence rehearsal document"
require_file "${runbook_path}" "runbook"
require_file "${rehearsal_path}" "customer-like rehearsal environment"
require_file "${smoke_path}" "runtime smoke bundle"
require_file "${handoff_path}" "operational evidence handoff pack"
require_executable "${record_chain_path}" "Phase 37 reviewed record-chain rehearsal verifier"
require_executable "${smoke_gate_path}" "Phase 37 runtime smoke gate"

required_headings=(
  "# Phase 37 Restore Rollback Upgrade Evidence Rehearsal"
  "## 1. Purpose and Boundary"
  "## 2. Prerequisites"
  "## 3. Rehearsal Flow"
  "## 4. Retained Manifest"
  "## 5. Fail-Closed Validation"
  "## 6. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${doc_path}" "${heading}" "Phase 37 release-gate rehearsal heading"
done

required_doc_phrases=(
  "This document defines the Phase 37 release-gate rehearsal for pre-change backup capture, restore validation, same-day rollback decision evidence, post-upgrade smoke, and retained handoff evidence."
  'The rehearsal is anchored to `docs/runbook.md`, `docs/deployment/customer-like-rehearsal-environment.md`, `docs/deployment/runtime-smoke-bundle.md`, and `docs/deployment/operational-evidence-handoff-pack.md`.'
  "The release gate proves that backup, restore, rollback, upgrade, smoke, and reviewed-record evidence stay explainable against the AegisOps authoritative record chain."
  "- a PostgreSQL-aware pre-change backup custody record;"
  "- the restore target and restore point selected for same-day rollback;"
  '- the seeded reviewed record-chain rehearsal result from `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`;'
  '- the runtime smoke gate output from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`; and'
  "Missing backup custody, restore target, rollback decision owner, smoke manifest, or reviewed record-chain evidence blocks the release gate until the prerequisite is supplied."
  "Rehearse restore against the reviewed recovery target and validate approval, evidence, execution, and reconciliation records against the reviewed record chain."
  "Record the same-day rollback decision, including whether rollback was not needed or which restore point and configuration revision were used."
  'Run the Phase 37 runtime smoke gate after restore, rollback, or upgrade where feasible and retain its `manifest.md`.'
  'Assemble the release-gate manifest and verify it with `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>`.'
  "The retained manifest is the handoff index for the release gate."
  "clean-state validation confirming no orphan record, partial durable write, half-restored state, or misleading handoff evidence survived a failed path"
  'The manifest must use repo-relative commands, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, and `<release-gate-manifest.md>`.'
  "The verifier fails closed when the rehearsal document is missing, required cross-links are missing, a retained manifest omits backup, restore, rollback, upgrade, smoke, reviewed-record, or clean-state evidence, placeholder values remain, or publishable guidance uses workstation-local absolute paths."
  "Zero-downtime deployment, HA, database clustering, vendor-specific backup product integration, direct backend exposure, optional-extension startup or upgrade gates, multi-customer evidence warehouses, and customer-private production access are out of scope."
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}" "Phase 37 release-gate rehearsal statement"
done

require_phrase "${runbook_path}" 'The Phase 37 restore, rollback, and upgrade evidence rehearsal in `docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md` is the reviewed release-gate path for tying pre-change backup custody, restore validation, rollback decision evidence, post-upgrade smoke, and retained handoff evidence together.' "runbook Phase 37 restore rollback upgrade evidence link"
require_phrase "${rehearsal_path}" 'Assemble and verify the restore, rollback, and upgrade release-gate manifest with `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>` before handoff closes.' "customer-like rehearsal release-gate manifest step"
require_phrase "${handoff_path}" 'For Phase 37 restore, rollback, and upgrade rehearsal, retain the release-gate manifest verified by `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>` so backup, restore, rollback, upgrade, smoke, reviewed-record, and clean-state evidence remain linked in one handoff index.' "handoff Phase 37 restore rollback upgrade evidence link"
require_phrase "${smoke_path}" 'For restore, rollback, and upgrade release-gate rehearsal, the smoke manifest is one referenced artifact in the retained release-gate manifest verified by `scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh --manifest <release-gate-manifest.md>`.' "runtime smoke release-gate manifest link"

for forbidden in "requires zero-downtime" "requires HA" "requires database clustering" "requires vendor-specific backup" "requires OpenSearch" "requires n8n" "requires Shuffle"; do
  if grep -Fqi -- "${forbidden}" "${doc_path}"; then
    echo "Forbidden Phase 37 release-gate rehearsal statement: ${forbidden}" >&2
    exit 1
  fi
done

reject_workstation_paths "Phase 37 release-gate rehearsal guidance" "${doc_path}" "${runbook_path}" "${rehearsal_path}" "${smoke_path}" "${handoff_path}"

if [[ -n "${manifest_path}" ]]; then
  require_file "${manifest_path}" "Phase 37 release-gate evidence manifest"
  reject_placeholders "${manifest_path}" "manifest"
  reject_workstation_paths "Phase 37 release-gate evidence manifest" "${manifest_path}"

  required_manifest_phrases=(
    "# Phase 37 Restore Rollback Upgrade Evidence Manifest"
    "Rehearsal owner:"
    "Maintenance window:"
    "Pre-change backup custody:"
    "Selected restore point:"
    "Restore target:"
    "Restore validation:"
    "Same-day rollback decision:"
    "Rollback evidence:"
    "Upgrade evidence:"
    "Post-upgrade smoke:"
    "Reviewed record-chain evidence:"
    "Clean-state validation:"
    "Evidence handoff:"
    "Next review:"
  )

  for phrase in "${required_manifest_phrases[@]}"; do
    require_phrase "${manifest_path}" "${phrase}" "Phase 37 release-gate evidence manifest statement"
  done
fi

echo "Phase 37 restore, rollback, upgrade, smoke, and handoff evidence rehearsal is documented and fail-closed."
