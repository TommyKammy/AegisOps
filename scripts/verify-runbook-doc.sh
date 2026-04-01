#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/runbook.md"

required_headings=(
  "## 1. Purpose and Status"
  "## 2. Startup"
  "## 3. Shutdown"
  "## 4. Restore"
  "## 5. Approval Handling"
  "## 6. Validation"
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

echo "Runbook document is present and limited to an approved skeleton."
