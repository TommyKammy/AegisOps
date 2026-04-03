#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/runbook.md"

required_headings=(
  "## 1. Purpose and Status"
  "## 2. Startup"
  "## 3. Shutdown"
  "## 4. Restore"
  "## 5. Approval Handling"
  "## 6. Validation"
  "### 6.1 Selected Slice and Preconditions"
  "### 6.2 Analyst Validation Path"
  "### 6.3 Required Evidence Review"
  "### 6.4 Disable and Rollback Path"
)

required_phrases=(
  "This runbook is an initial skeleton for approved future operational procedures."
  "It does not claim production completeness and does not authorize environment-specific commands."
  "The approved baseline requires explicit approval for SOAR workflows that perform write or destructive actions by default."
  "Detailed startup steps are intentionally deferred until implementation artifacts and validation procedures exist."
  "Detailed shutdown steps are intentionally deferred until implementation artifacts and validation procedures exist."
  "Detailed restore steps are intentionally deferred until implementation artifacts and validation procedures exist."
  "Approval handling procedures must preserve human review, auditability, and the separation between detection and execution."
  "Validation steps must be documented and repeatable before this runbook can be treated as an operational procedure."
  'The selected Phase 6 validation slice is limited to the Windows security and endpoint telemetry family and the three reviewed detector artifacts under `opensearch/detectors/windows-security-and-endpoint/`.'
  "This runbook section is limited to replay validation, staging-only detector review, and read-only or notify-only workflow review during business hours."
  'Operators must review replay evidence from `ingest/replay/windows-security-and-endpoint/normalized/success.ndjson`, the staging-only detector metadata, and the read-only or notify-only workflow assets before treating the slice as validated.'
  'If validation fails, disable the selected slice by keeping the detector artifacts out of production activation and by withdrawing `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json` from the active workflow set until the issue is corrected and re-reviewed.'
  "The selected slice remains business-hours oriented and does not imply 24x7 monitoring, production write behavior, or uncontrolled activation."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing runbook document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing runbook heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing runbook statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Runbook document is present and covers the approved Phase 6 analyst validation and rollback slice."
