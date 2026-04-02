#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/secops-domain-model.md"

required_headings=(
  "# AegisOps SecOps Domain Model"
  "## 1. Purpose"
  "## 2. Core Domain Objects"
  "## 3. Relationship and State Boundaries"
  "## 4. Baseline System of Record"
  "## 5. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the first-class SecOps domain model for the AegisOps baseline."
  "This document defines baseline semantics, ownership boundaries, and state transitions only. It does not introduce runtime behavior, workflow automation, or architecture changes."
  '| `Raw Event` |'
  '| `Normalized Event` |'
  '| `Detection Rule` |'
  '| `Finding` |'
  '| `Alert` |'
  '| `Case` |'
  '| `Incident` |'
  '| `Asset` |'
  '| `Identity` |'
  '| `Evidence` |'
  '| `Action Request` |'
  '| `Approval Decision` |'
  '| `Action Execution` |'
  '| `Disposition` |'
  "A finding is the normalized analytic assertion that detection logic matched relevant telemetry."
  "An alert is the routed operator-facing notification or queue item created from one or more findings after baseline triage policy decides analyst attention is required."
  "A case is the investigation record that groups alerts, evidence, analyst notes, and response coordination for one work item."
  "An incident is the higher-order security event declaration used when one or more cases represent a material security event that needs coordinated operational handling."
  "An approval decision records whether a specific action request is authorized, rejected, or expired."
  "An action execution records the actual downstream attempt or completion state for an approved or explicitly allowed action request."
  "OpenSearch findings, n8n workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states."
  '| `Finding` | OpenSearch detection and analytics plane |'
  '| `Alert` | Future AegisOps alert routing and triage control layer |'
  '| `Case` | Future AegisOps case management control layer |'
  '| `Approval Decision` | Future AegisOps approval control layer |'
  '| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state |'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing SecOps domain model document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing SecOps domain model heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing SecOps domain model statement: ${phrase}" >&2
    exit 1
  fi
done

echo "SecOps domain model document is present and defines the required objects, boundaries, and baseline ownership."
