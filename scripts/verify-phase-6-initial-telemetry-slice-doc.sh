#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-6-initial-telemetry-slice.md"

required_headings=(
  "# AegisOps Phase 6 Initial Telemetry Slice"
  "## 1. Purpose"
  "## 2. Selected Initial Telemetry Family"
  "## 3. Selected Initial Detection Use Cases"
  "## 4. Selection Rationale"
  "## 5. Scope Guardrails"
)

required_phrases=(
  "This document selects the single initial telemetry family and first detection use cases for the Phase 6 validated slice."
  "The selected initial telemetry family for the Phase 6 slice is Windows security and endpoint telemetry."
  "Phase 6 starts with one telemetry family only."
  "The initial use cases below are intentionally limited to single-event detections that can be reviewed during business hours and exercised through replay."
  "The Phase 6 slice is limited to these three initial detection use cases:"
  "Privileged group membership change"
  "Audit log cleared"
  "New local user created"
  "Each selected use case can be exercised with replayable Windows event samples and handled through read-only analyst workflow steps before any approval-bound response exists."
  "Windows telemetry is the best first proof of the Phase 5 contracts because it exercises actor identity, host identity, provenance, timestamp semantics, and Sigma-compatible single-event detection patterns in one family."
  "Network telemetry is deferred because volume, directionality, and product variance would broaden parser and tuning scope too early."
  "Linux telemetry is deferred because initial source heterogeneity would widen normalization and replay coverage before the first vertical slice is proven."
  "SaaS audit telemetry is deferred because provider-specific action semantics would force early cross-provider narrowing inside a family that is still too broad for the first validated slice."
  "No additional telemetry families, correlation logic, threshold-based analytics, response automation, or after-hours operating promises are included in this slice."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 6 initial telemetry slice document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing Phase 6 telemetry slice heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing Phase 6 telemetry slice statement: ${phrase}" >&2
    exit 1
  fi
done

use_case_count="$(grep -Ec '^[[:space:]]*[0-9]+\. ' "${doc_path}")"
if [[ "${use_case_count}" -ne 3 ]]; then
  echo "Expected exactly three numbered initial detection use cases, found ${use_case_count}." >&2
  exit 1
fi

echo "Phase 6 initial telemetry slice document is present and constrained to one family with three replayable, reviewable use cases."
