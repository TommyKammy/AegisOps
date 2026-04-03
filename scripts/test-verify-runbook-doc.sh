#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-runbook-doc.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
}

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/runbook.md"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_doc "${valid_repo}" '# AegisOps Runbook Skeleton

This runbook is an initial skeleton for approved future operational procedures.

It supplements `docs/requirements-baseline.md` by reserving a structured home for startup, shutdown, restore, approval handling, and validation guidance as implementation artifacts mature.

It does not claim production completeness and does not authorize environment-specific commands.

## 1. Purpose and Status

This document exists to define the minimum approved structure for future operator procedures without implying that those procedures are complete today.

## 2. Startup

Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist.

## 3. Shutdown

Detailed shutdown steps are intentionally deferred until implementation artifacts and validation procedures exist.

## 4. Restore

Detailed restore steps are intentionally deferred until implementation artifacts and validation procedures exist.

## 5. Approval Handling

The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default.

Approval handling procedures must preserve human review, auditability, and the separation between detection and execution.

## 6. Validation

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure.

The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.

This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours.

### 6.1 Selected Slice and Preconditions

Preconditions are documented for the selected slice only.

### 6.2 Analyst Validation Path

Analyst validation remains replay-oriented and business-hours only.

### 6.3 Required Evidence Review

Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.

### 6.4 Disable and Rollback Path

If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.

The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation.'
assert_passes "${valid_repo}"

missing_rollback_repo="${workdir}/missing-rollback"
create_repo "${missing_rollback_repo}"
write_doc "${missing_rollback_repo}" '# AegisOps Runbook Skeleton

This runbook is an initial skeleton for approved future operational procedures.

It supplements `docs/requirements-baseline.md` by reserving a structured home for startup, shutdown, restore, approval handling, and validation guidance as implementation artifacts mature.

It does not claim production completeness and does not authorize environment-specific commands.

## 1. Purpose and Status

This document exists to define the minimum approved structure for future operator procedures without implying that those procedures are complete today.

## 2. Startup

Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist.

## 3. Shutdown

Detailed shutdown steps are intentionally deferred until implementation artifacts and validation procedures exist.

## 4. Restore

Detailed restore steps are intentionally deferred until implementation artifacts and validation procedures exist.

## 5. Approval Handling

The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default.

Approval handling procedures must preserve human review, auditability, and the separation between detection and execution.

## 6. Validation

Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure.

The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.

This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours.

### 6.1 Selected Slice and Preconditions

Preconditions are documented for the selected slice only.

### 6.2 Analyst Validation Path

Analyst validation remains replay-oriented and business-hours only.

### 6.3 Required Evidence Review

Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.

### 6.4 Disable and Rollback Path

The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation.'
assert_fails_with "${missing_rollback_repo}" 'Missing runbook statement: If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.'

echo "Runbook verifier tests passed."
