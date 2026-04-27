#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
checklist_path="${repo_root}/docs/deployment/pilot-readiness-checklist.md"
runbook_path="${repo_root}/docs/runbook.md"
release_inventory_path="${repo_root}/docs/deployment/single-customer-release-bundle-inventory.md"
release_handoff_path="${repo_root}/docs/deployment/release-handoff-evidence-package.md"
smoke_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"
detector_handoff_path="${repo_root}/docs/detector-activation-evidence-handoff.md"
coordination_path="${repo_root}/docs/operations-zammad-live-pilot-boundary.md"
assistant_path="${repo_root}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
operational_handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
verifier_test_path="${repo_root}/scripts/test-verify-pilot-readiness-checklist.sh"

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

reject_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if grep -Fqi -- "${phrase}" "${path}"; then
    echo "Forbidden ${description}: ${phrase}" >&2
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

require_file "${checklist_path}" "pilot readiness checklist"
require_file "${runbook_path}" "runbook"
require_file "${release_inventory_path}" "single-customer release bundle inventory"
require_file "${release_handoff_path}" "release handoff evidence package"
require_file "${smoke_path}" "runtime smoke bundle"
require_file "${detector_handoff_path}" "detector activation evidence handoff manifest"
require_file "${coordination_path}" "Zammad live pilot boundary"
require_file "${assistant_path}" "assistant boundary"
require_file "${operational_handoff_path}" "operational evidence handoff pack"
require_file "${verifier_test_path}" "pilot readiness checklist verifier tests"

required_headings=(
  "# Single-Customer Pilot Readiness Checklist and Entry Criteria"
  "## 1. Purpose and Boundary"
  "## 2. Entry Decision Summary"
  "## 3. Readiness Checklist"
  "## 4. Required Entry Evidence"
  "## 5. Known Limitations, Retention, and Evidence Handoff"
  "## 6. Blocking Outcomes"
  "## 7. Verification"
  "## 8. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${checklist_path}" "${heading}" "pilot readiness checklist heading"
done

required_checklist_phrases=(
  "This document defines the reviewed entry checklist for starting one single-customer pilot."
  "The entry decision is a reviewed go, no-go, or go-with-explicit-limitations decision for one customer environment; it is not a compliance certification, multi-customer rollout approval, SLA commitment, or 24x7 support promise."
  "The pilot may start only when release readiness, runtime smoke, detector activation scope, coordination pilot scope, assistant limitations, data retention, and evidence handoff are reviewed together for the same release identifier."
  'Release readiness must be bound to `docs/deployment/single-customer-release-bundle-inventory.md` and `docs/deployment/release-handoff-evidence-package.md` for the same `aegisops-single-customer-<repository-revision>` release identifier.'
  'Runtime smoke must pass through `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` and retain the smoke `manifest.md` as entry evidence.'
  'Detector activation scope must follow `docs/detector-activation-evidence-handoff.md` and name only the reviewed candidate rules, fixture evidence, activation owner, disable owner, rollback owner, expected alert volume, false-positive review, and next-review date accepted for the pilot.'
  'Coordination scope must follow `docs/operations-zammad-live-pilot-boundary.md`; Zammad remains link-first, coordination-only, and non-authoritative for AegisOps case, action, approval, execution, and reconciliation records.'
  'Zammad coordination rehearsal evidence must include the checked available, degraded, and unavailable scenarios from `control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json` so stale reads, mismatched ticket identifiers, and missing or placeholder credentials remain visible without becoming AegisOps truth.'
  'Assistant output remains advisory-only and non-authoritative; it must stay grounded in reviewed control-plane records and linked evidence and must not approve, execute, reconcile, close, or widen pilot scope.'
  "Known limitations must be explicit, reviewed, and tied to the entry decision, including whether each limitation blocks pilot start, allows pilot start with a follow-up owner, or requires rollback or disable evidence."
  "Data retention for the pilot is bounded to the current release handoff, runtime smoke manifest, detector activation evidence handoff, Zammad coordination reference, assistant limitation note, and next health review expectation; it is not an unlimited archive."
  "Evidence handoff must name the release handoff record, runtime smoke manifest, detector activation handoff, coordination pilot status, assistant limitation statement, known-limitations review, handoff owner, and next health review."
  "Missing release readiness, failed runtime smoke, missing detector activation owner, missing disable or rollback owner, missing Zammad credential custody, missing assistant limitation statement, missing known-limitations review, missing evidence handoff owner, or mixed release identifiers blocks pilot entry."
  'Verify this checklist with `scripts/verify-pilot-readiness-checklist.sh`.'
  'Negative validation for the verifier is `scripts/test-verify-pilot-readiness-checklist.sh`.'
  "Formal compliance certification, multi-customer rollout, SLA or 24x7 support promise, external archive platform design, customer-private production access, optional-extension launch gates, direct backend exposure, ticket-system authority, and assistant-owned workflow authority are out of scope."
)

for phrase in "${required_checklist_phrases[@]}"; do
  require_phrase "${checklist_path}" "${phrase}" "pilot readiness checklist statement"
done

require_phrase "${runbook_path}" 'Before starting a single-customer pilot, review `docs/deployment/pilot-readiness-checklist.md` and verify it with `scripts/verify-pilot-readiness-checklist.sh` so release readiness, runtime smoke, detector activation scope, Zammad coordination scope, assistant limitations, data retention, known limitations, and evidence handoff are decided together.' "runbook pilot readiness link"
require_phrase "${release_inventory_path}" 'Pilot entry must use `docs/deployment/pilot-readiness-checklist.md` after the single-customer release bundle inventory is bound to the same `aegisops-single-customer-<repository-revision>` release identifier.' "release inventory pilot readiness link"
require_phrase "${release_handoff_path}" 'The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this release handoff package as the reviewed release-readiness and known-limitations evidence source for the pilot entry decision.' "release handoff pilot readiness link"
require_phrase "${smoke_path}" 'The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` treats the retained runtime smoke `manifest.md` from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` as required entry evidence.' "runtime smoke pilot readiness link"
require_phrase "${detector_handoff_path}" 'The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this detector activation evidence handoff as the bounded detector scope, owner, rollback, disable, expected-volume, false-positive, and known-limitation evidence for pilot entry.' "detector handoff pilot readiness link"
require_phrase "${coordination_path}" 'The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this Zammad-first boundary as the coordination pilot scope and credential-custody prerequisite for pilot entry.' "coordination pilot readiness link"
require_phrase "${assistant_path}" 'The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` must keep this assistant boundary advisory-only and non-authoritative for pilot entry.' "assistant pilot readiness link"
require_phrase "${operational_handoff_path}" 'The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` is the reviewed entry decision surface that points operators to the retained release, smoke, detector, coordination, limitation, and evidence handoff records before pilot start.' "operational handoff pilot readiness link"

for forbidden in \
  "compliance certification is complete" \
  "multi-customer rollout is approved" \
  "24x7 support is promised" \
  "SLA is promised" \
  "ticket system is authoritative" \
  "assistant may approve" \
  "assistant may execute" \
  "detector activation is automatic" \
  "optional extensions are required for pilot"; do
  reject_phrase "${checklist_path}" "${forbidden}" "pilot readiness checklist statement"
done

reject_workstation_paths "pilot readiness guidance" \
  "${checklist_path}" \
  "${runbook_path}" \
  "${release_inventory_path}" \
  "${release_handoff_path}" \
  "${smoke_path}" \
  "${detector_handoff_path}" \
  "${coordination_path}" \
  "${assistant_path}" \
  "${operational_handoff_path}"

echo "Pilot readiness checklist, entry criteria, cross-links, limitations, and evidence handoff expectations are present and bounded."
