#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/requirements-baseline.md"

required_phrases=(
  "# AegisOps"
  "## Platform Requirements Baseline"
  "This document defines the **non-negotiable implementation baseline** for **AegisOps** as a **governed control plane above commodity detection and automation substrates**."
  "AegisOps is a governed SecOps control plane."
  "AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model."
  "AegisOps owns the authoritative platform records and policy decisions for:"
  "- Alert"
  "- Case"
  "- Evidence"
  "- Approval Decision"
  "- Action Request"
  "- Action Execution"
  "- Reconciliation"
  "| AegisOps control plane | Alert, case, evidence, observation, lead, recommendation, approval, action-request, action-execution, hunt, AI-trace, reconciliation, and append-only lifecycle-transition ownership |"
  "AegisOps owns approval decisions, action intent, action-execution truth, evidence linkage, reconciliation, and the append-only lifecycle transition history paired with reviewed current-state records"
  "Authoritative backup and restore workflows MUST preserve the reviewed current-state record chain together with its append-only lifecycle transition history when that history is part of the reviewed control-plane surface"
  "Analytic Signals are upstream inputs to AegisOps, not the durable system of record for analyst workflow, approval state, evidence custody, action-execution state, or reconciliation."
  "Upstream detections, findings, correlations, and product-native alerting artifacts from external substrates are treated as **Analytic Signals**."
  "OpenSearch, Sigma, and n8n are **not** co-equal product cores for AegisOps."
  "OpenSearch MAY be used as an optional or transitional analytics substrate."
  "Sigma MAY be used as an optional or transitional rule-definition format."
  "n8n MAY be used as an optional, transitional, or experimental execution substrate."
  "AegisOps will **not** rebuild Wazuh-class detection breadth in-house."
  "AegisOps will **not** rebuild Shuffle-class routine automation breadth in-house."
  "The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners."
  "The target operating assumption is business-hours review with explicit after-hours escalation, not a 24x7 staffed SOC."
  "The repository structure and approval boundary in this document remain reviewable baseline constraints."
  "This rebaseline does **not** by itself approve runtime implementation changes, new adapters, or repository-structure expansion."
)

forbidden_phrases=(
  "**(OpenSearch + Sigma + n8n)**"
  "The platform is built on the following core components:"
  "Alert-to-SOAR integration with approval gating"
  "OpenSearch finding"
  "OpenSearch findings"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing requirements baseline document: ${doc_path}" >&2
  exit 1
fi

contains_phrase() {
  local phrase="$1"

  grep -Fq -- "${phrase}" < <(tr -d $'\r' < "${doc_path}")
}

for phrase in "${required_phrases[@]}"; do
  if ! contains_phrase "${phrase}"; then
    echo "Missing requirements baseline statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${forbidden_phrases[@]}"; do
  if contains_phrase "${phrase}"; then
    echo "Forbidden legacy requirements baseline statement present: ${phrase}" >&2
    exit 1
  fi
done

echo "Requirements baseline reflects the governed control-plane thesis and keeps the approval boundary explicit."
