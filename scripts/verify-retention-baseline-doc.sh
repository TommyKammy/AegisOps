#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/retention-evidence-and-replay-readiness-baseline.md"

required_headings=(
  "# AegisOps Retention, Evidence Lifecycle, and Replay Readiness Baseline"
  "## 1. Purpose"
  "## 2. Retention Classes"
  "## 3. Replay Dataset and Restore Readiness Expectations"
  "## 4. Evidence Lifecycle and Legal-Hold Baseline"
  "## 5. Lifecycle Policy Constraints"
  "## 6. Baseline Alignment Notes"
)

required_phrases=(
  '| `Raw Event` |'
  '| `Normalized Event` |'
  '| `Finding` |'
  '| `Alert` |'
  '| `Evidence` |'
  '| `Approval Decision` |'
  '| `Action Execution` |'
  "Replay-capable datasets must be retained long enough to support parser validation, rule validation, and targeted historical reprocessing for approved investigations and recovery exercises."
  "Restore readiness must assume application-aware restore procedures for OpenSearch, PostgreSQL, and future platform-owned control records rather than treating hypervisor snapshots as the primary recovery model."
  "Evidence retention must preserve chain-of-custody context, source provenance, review references, and legal-hold status long enough to support audit, investigation, and post-incident review."
  "Legal hold must suspend ordinary expiration for specifically scoped evidence and related approval or execution records until the hold is explicitly released through approved process."
  "This baseline defines policy-level hot, warm, cold, or rollover expectations only. It does not introduce live ILM policies, shard counts, index templates, storage tier automation, or production retention settings in this phase."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing retention baseline document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing retention baseline heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing retention baseline statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Retention, evidence lifecycle, and replay readiness baseline document covers the required rules."
