#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/secops-business-hours-operating-model.md"

required_headings=(
  "# AegisOps Business-Hours SecOps Daily Operating Model"
  "## 1. Purpose"
  "## 2. Operating Assumptions"
  "## 3. Daily Analyst Workflow"
  "## 4. Approval, Timeout, and Manual Fallback Expectations"
  "## 5. After-Hours and Handoff Model"
  "## 6. Required Records and Decision Points"
  "## 7. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the business-hours SecOps daily operating model for the AegisOps baseline."
  "This model assumes business-hours analyst coverage rather than 24x7 staffed monitoring."
  "Finding or alert intake enters the analyst review queue for the next business-hours review cycle unless an explicitly defined escalation path applies."
  "The analyst begins by validating whether the incoming finding or alert is in scope, duplicated, or obviously explained by known benign context."
  "A case is created when the work requires durable ownership, evidence capture, approval tracking, cross-shift visibility, or coordinated follow-up beyond the alert record itself."
  "The analyst records the recommended action, target scope, justification, and required approver before any approval-bound response is requested."
  "Approval timeout must leave the action request in a non-executed state and force explicit analyst re-review during business hours before any later execution attempt."
  "Manual fallback may be used when the approved workflow path is unavailable, but the same approval decision, execution record, and post-action evidence requirements still apply."
  "After hours, AegisOps does not imply an always-on analyst at the console."
  "After-hours handling must distinguish between work that can wait for the next business-hours review window and work that requires explicit escalation to an on-call or separately designated human owner."
  "Business-hours handoff must preserve queue state, open cases, pending approvals, expired approvals, and follow-up tasks so the next analyst can continue without reconstructing context from raw system logs."
  '| `Alert or Finding Record` |'
  '| `Case Record` |'
  '| `Approval Decision Record` |'
  '| `Action Execution Record` |'
  '| `Closure or Disposition Record` |'
  "No part of this operating model creates a 24x7 staffing promise, an automatic destructive-action path, or a dependency on unsupported live-response coverage."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing business-hours operating model document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing business-hours operating model heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing business-hours operating model statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Business-hours SecOps operating model document is present and defines the required workflow, after-hours handling, and audit records."
