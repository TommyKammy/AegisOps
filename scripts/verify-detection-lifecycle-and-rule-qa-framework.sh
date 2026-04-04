#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/detection-lifecycle-and-rule-qa-framework.md"

required_headings=(
  "# AegisOps Detection Lifecycle and Rule QA Framework"
  "## 1. Purpose"
  "## 2. Scope and Non-Goals"
  "## 3. Lifecycle States"
  "## 4. State Transition Expectations"
  "## 5. Minimum QA Evidence Before Activation"
  "## 6. Ownership, Review, and Expiry Expectations"
  "## 7. Post-Deploy Review and Rollback Expectations"
  "## 8. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the baseline lifecycle states and minimum quality-assurance evidence required before AegisOps detection content can move from proposal to activation, deprecation, and retirement."
  "It applies to Sigma detection rules, OpenSearch detector artifacts, supporting validation notes, and future detection metadata that govern whether reviewed content is ready for activation decisions."
  "This framework defines review and readiness expectations only. It does not authorize live detector activation, bypass staging, or approve production rollout without separate implementation work."
  'The lifecycle must distinguish at least `draft`, `candidate`, `staging`, `active`, `deprecated`, and `retired` detection content states.'
  '| `draft` | Initial proposal or substantial rewrite that is not yet eligible for activation review. |'
  '| `candidate` | Reviewable detection content with assigned ownership and documented intent, but not yet approved for staging activation. |'
  '| `staging` | Content approved for controlled validation in a staging environment or test index only. |'
  '| `active` | Content approved for production activation with documented evidence and follow-up obligations. |'
  '| `deprecated` | Content that remains deployed or historically referenced temporarily while replacement or removal is coordinated. |'
  '| `retired` | Content removed from active use and preserved only for audit, history, or reference. |'
  'Detection content must not move to `staging` until source prerequisites, field coverage expectations, replay data, and review ownership are explicitly documented.'
  'Detection content must not move to `active` until replay or staged validation evidence, expected-volume review, and false-positive review are recorded and reviewable.'
  'Staging readiness is sufficient for controlled translation and validation only when source prerequisites and activation-gating field dependencies are explicit and reviewable.'
  'Production activation requires detection-ready source evidence for activation-gating dependencies and must not rely on schema-reviewed coverage alone.'
  "Activation readiness requires evidence for source prerequisite checks, canonical field coverage checks, replay or staged tests, expected alert volume review, and false-positive review."
  "Source prerequisite checks must confirm that the required source family is admitted under the source onboarding contract, that required indices or datasets exist, and that the rule does not depend on undeclared telemetry."
  "Field coverage checks must identify the match-required fields, triage-required fields, activation-gating fields, confidence-degrading gaps, and whether each missing field blocks staging or active use."
  "Replay or staged test evidence must show that the detection logic was exercised against representative data before activation decisions are made."
  "Expected-volume review must document whether the projected finding or alert volume is acceptable for the initial operating model and what assumptions were used."
  "False-positive review must record known benign triggers, planned tuning or suppression constraints, and whether analyst review load is acceptable."
  "Each detection change must declare an owner, a required reviewer, an expiry or next-review date, and the rollback expectation for disabling or reverting the change if post-deploy behavior is unacceptable."
  "Post-deploy review must verify observed behavior after activation, compare actual volume against the staged expectation, and confirm whether tuning, suppression, deprecation, or retirement is required."
  "Rollback expectations must preserve the ability to disable or revert a detection change without implying autonomous response or staging bypass."
  'This framework remains aligned with `docs/requirements-baseline.md`, `docs/source-onboarding-contract.md`, `docs/sigma-to-opensearch-translation-strategy.md`, and `docs/secops-domain-model.md`.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing detection lifecycle and rule QA framework document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing detection lifecycle framework heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing detection lifecycle framework statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Detection lifecycle and rule QA framework document is present and defines lifecycle states, activation evidence, and follow-up expectations."
