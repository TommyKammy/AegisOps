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
  "## 5. Promotion and Correlation Rules"
  "## 6. Grouping, Deduplication, and Case Creation Expectations"
  "## 7. Disposition and Closure Taxonomy"
  "## 8. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the first-class SecOps domain model for the AegisOps baseline."
  "This document defines baseline semantics, ownership boundaries, and state transitions only. It does not introduce runtime behavior, workflow automation, or architecture changes."
  '| `Raw Event` |'
  '| `Normalized Event` |'
  '| `Detection Rule` |'
  '| `Finding` |'
  '| `Correlation` |'
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
  "Correlation is the explicit relationship that links related findings, alerts, cases, assets, or identities because they share meaningful operator-facing context."
  "An alert is the routed operator-facing notification or queue item created from one or more findings after baseline triage policy decides analyst attention is required."
  "A case is the investigation record that groups alerts, evidence, analyst notes, and response coordination for one work item."
  "An incident is the higher-order security event declaration used when one or more cases represent a material security event that needs coordinated operational handling."
  "An approval decision records whether a specific action request is authorized, rejected, or expired."
  "An action execution records the actual downstream attempt or completion state for an approved or explicitly allowed action request."
  "OpenSearch findings, n8n workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states."
  '| `Finding` | OpenSearch detection and analytics plane |'
  '| `Correlation` | Future AegisOps correlation and triage control layer |'
  '| `Alert` | Future AegisOps alert routing and triage control layer |'
  '| `Case` | Future AegisOps case management control layer |'
  '| `Approval Decision` | Future AegisOps approval control layer |'
  '| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state |'
  "A finding promotes to an alert only when triage policy determines that analyst attention, tracking, notification, or downstream workflow handling is required."
  "Correlation links records by shared context, but it does not by itself create an alert, open a case, or declare an incident."
  "A case must not be created for every alert by default."
  "Deduplication means additional findings are attached to an existing alert or case when they restate the same analytic claim against materially the same operational target within the active review window."
  "A new alert must be created instead of deduplicating when severity, target scope, response owner, or review window changes enough that analyst handling would differ."
  "A case is created when analyst work requires durable ownership, evidence collection, note-taking, handoff, or coordinated response beyond the alert record itself."
  "An incident is declared only when one or more cases represent a material security event that requires coordinated operational handling beyond a single investigative work item."
  '| `False Positive` | The analytic claim was incorrect.'
  '| `Benign Positive` | The activity occurred as detected but does not represent harmful or policy-violating behavior in context.'
  '| `Duplicate` | The record does not represent new work because another active or closed record already tracks the same claim.'
  '| `Expected Administrative Activity` | The activity is legitimate administrative, maintenance, or approved operational work that should remain distinguishable from suspicious behavior.'
  '| `Accepted Risk` | The activity or exposure is known and consciously accepted by the accountable owner, so no further investigative escalation is required under the current baseline.'
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
