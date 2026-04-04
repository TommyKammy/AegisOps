#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/sigma-to-opensearch-translation-strategy.md"

required_headings=(
  "# AegisOps Sigma-to-OpenSearch Translation Strategy"
  "## 1. Purpose"
  "## 2. Baseline Translation Boundary"
  "## 3. Supported Sigma Subset for the Approved Baseline"
  "## 4. Required Rule Metadata and Source Prerequisites"
  "## 5. Unsupported and Deferred Sigma Feature Matrix"
  "## 6. OpenSearch-Native Fallback Path"
  "## 7. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the approved Sigma-to-OpenSearch translation strategy for the AegisOps baseline."
  "It makes the supported Sigma subset, required metadata, deferred features, and OpenSearch-native fallback path explicit before runtime detector implementation begins."
  "This strategy defines translation scope and review boundaries only. It does not claim full Sigma parity and does not approve automatic detector generation or production activation."
  "AegisOps supports only single-rule, single-event Sigma detections whose logic can be translated into reviewable OpenSearch detector content without changing the rule's meaning."
  'The approved baseline supports selection-based field matching, boolean condition composition using `and`, `or`, and `not`, and stable comparisons on normalized fields that have documented source coverage.'
  "The baseline does not support Sigma correlation, aggregations, temporal counting semantics, cross-index joins, multi-source dependencies, or field logic that depends on unsupported modifiers without a separate approved design."
  "Each rule proposed for translation must declare rule identity, owner, severity, purpose, ATT&CK mapping, split field semantics, source-family prerequisites, and known false-positive considerations."
  'A source family that remains `schema-reviewed` may be sufficient for staging translation review only when the rule declares which fields are match-required, triage-required, activation-gating, or confidence-degrading.'
  'Production activation requires `detection-ready` source evidence for every activation-gating dependency and must not treat `schema-reviewed` coverage alone as sufficient.'
  "| Supported for baseline translation | Simple single-event selections on normalized fields; boolean combinations that preserve straight-through detector meaning |"
  "| Deferred pending separate design | Correlation blocks; aggregation or threshold semantics; temporal sequences; multi-source joins |"
  "| Forbidden for straight-through translation | Content that requires hidden enrichment assumptions, undocumented field remapping, or runtime behavior outside approved OpenSearch detector responsibilities |"
  "When a detection requirement cannot be translated safely from the approved Sigma subset, the detection must remain OpenSearch-native and carry explicit documentation that Sigma is not the source of truth for that rule."
  "OpenSearch-native fallback content must still preserve owner, purpose, source prerequisites, split field semantics, validation evidence, and false-positive notes so review standards remain consistent."
  'This strategy remains aligned with `docs/requirements-baseline.md`, `docs/source-onboarding-contract.md`, and `docs/secops-domain-model.md`.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Sigma-to-OpenSearch translation strategy document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing Sigma-to-OpenSearch strategy heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing Sigma-to-OpenSearch strategy statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Sigma-to-OpenSearch translation strategy document is present and defines the supported subset, deferred matrix, and fallback path."
