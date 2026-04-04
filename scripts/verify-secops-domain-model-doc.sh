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
  '| `Hunt` |'
  '| `Hunt Hypothesis` |'
  '| `Hunt Run` |'
  '| `Observation` |'
  '| `Lead` |'
  '| `Recommendation` |'
  '| `AI Trace` |'
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
  "A hunt is an analyst-directed exploration record created to test a threat hypothesis or investigate suspicious conditions beyond deterministic detection output."
  "A hunt hypothesis is the explicit statement of what the analyst believes may be happening, why it is worth testing, and what evidence or observations would support or refute it."
  "A hunt run is one bounded execution of a specific hunt hypothesis against a defined scope, time window, dataset, or query plan."
  "An observation is a recorded fact, pattern, or notable condition gathered during hunting or investigation that may inform later judgment but is not itself a deterministic detection claim."
  "A lead is a triage-worthy investigative signal derived from one or more observations, findings, or contextual facts that justifies additional analyst attention."
  "A recommendation is a proposed analyst or system action derived from findings, hunt conclusions, or AI-assisted interpretation that still requires human review within the appropriate approval boundary."
  "An AI trace is the preserved record of AI-assisted interpretation inputs, prompts, model outputs, confidence notes, and review context associated with a SecOps record."
  "Correlation is the explicit relationship that links related findings, alerts, cases, assets, or identities because they share meaningful operator-facing context."
  "An observation may support a finding or a lead, but it is not itself a finding because it does not assert that reviewed detection logic matched."
  "An observation may attach to a hunt run, alert, case, or stand-alone investigative thread, but attachment does not convert the observation into evidence custody, alert state, or case state."
  "A lead may promote into alert or case work when triage determines the signal warrants tracked investigation, but the lead remains distinct from the alert or case record it informs."
  "The lead record remains the system of record for the pre-promotion hypothesis, triage rationale, and promotion decision. AI trace text, case notes, or alert notes may reference that decision, but they must not replace the lead record itself."
  "A recommendation may attach to a hunt, hunt run, lead, alert, or case, but it remains advisory context until an explicit downstream task, approval, or action-request record is created."
  "An AI trace is not evidence. It preserves how AI-assisted interpretation was produced and reviewed, while evidence preserves the underlying supporting artifacts and chain of custody."
  "An AI trace may attach to a hunt, hunt run, observation, lead, recommendation, alert, or case, but it does not own the lifecycle of those records and must not become the implicit source of truth for promotion, approval, or closure."
  "AI-assisted interpretation may summarize, rank, or recommend, but it must not overwrite deterministic finding output, evidence custody, approval decisions, or action execution records."
  "An alert is the routed operator-facing notification or queue item created from one or more findings after baseline triage policy decides analyst attention is required."
  "A case is the investigation record that groups alerts, evidence, analyst notes, and response coordination for one work item."
  "An incident is the higher-order security event declaration used when one or more cases represent a material security event that needs coordinated operational handling."
  "An approval decision records whether a specific action request is authorized, rejected, or expired."
  "An action execution records the actual downstream attempt or completion state for an approved or explicitly allowed action request."
  "OpenSearch findings, n8n workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states."
  '| `Finding` | OpenSearch detection and analytics plane |'
  '| `Hunt` | Future AegisOps hunt management control layer |'
  '| `Hunt Hypothesis` | Future AegisOps hunt management control layer |'
  '| `Hunt Run` | Future AegisOps hunt management control layer |'
  '| `Observation` | Future AegisOps hunt and investigation record layer |'
  '| `Lead` | Future AegisOps triage and investigation control layer |'
  '| `Recommendation` | Future AegisOps analyst decision support control layer |'
  '| `AI Trace` | Future AegisOps AI interpretation record layer |'
  '| `Correlation` | Future AegisOps correlation and triage control layer |'
  '| `Alert` | Future AegisOps alert routing and triage control layer |'
  '| `Case` | Future AegisOps case management control layer |'
  '| `Approval Decision` | Future AegisOps approval control layer |'
  '| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state |'
  "A finding promotes to an alert only when triage policy determines that analyst attention, tracking, notification, or downstream workflow handling is required."
  "Finding-to-alert routing must preserve the distinction between the upstream finding, any distinct analytic signal emitted by OpenSearch alerting or correlation logic, and the downstream alert record created for analyst work."
  "A finding identifier, an analytic signal identifier, and an alert identifier are related references, not interchangeable lifecycle keys."
  "A hunt may produce observations, leads, recommendations, or supporting context for findings, alerts, and cases, but hunt records do not replace those records."
  "A lead promotes to an alert only when triage decides the investigative signal requires durable analyst queueing or response handling."
  "A lead may be attached directly to an existing case when the signal materially advances an active investigation without requiring a separate alert lifecycle."
  "Lead promotion must preserve explicit linkage from the lead to the destination alert or case so future workflow and schema work can reconstruct why tracked investigation began without mining case notes or AI trace history."
  "Correlation links records by shared context, but it does not by itself create an alert, open a case, or declare an incident."
  "A case must not be created for every alert by default."
  "Deduplication means additional findings are attached to an existing alert or case when they restate the same analytic claim against materially the same operational target within the active review window."
  "When upstream analytics restate the same claim without materially changing analyst work, the control plane must update or link the existing alert rather than minting a new alert identifier."
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
