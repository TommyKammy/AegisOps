#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/safe-query-gateway-and-tool-policy.md"

required_headings=(
  "# AegisOps Safe Query Gateway and AI Hunt Tool Policy"
  "## 1. Purpose"
  "## 2. Safe Query Gateway Boundary"
  "## 3. Structured Query Intent Contract"
  "## 4. Validation and Deterministic Query Generation"
  "## 5. Allowlists and Budget Limits"
  "## 6. Citation-Bearing Response Contract"
  "## 7. Tool Policy Trust Classes"
  "## 8. Failure Handling"
  "## 9. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the baseline Safe Query Gateway and tool policy for future AI-assisted hunt workflows."
  "This document defines request, validation, and trust-boundary policy only. It does not authorize direct AI access to OpenSearch, unrestricted public web access, or execution-capable tools."
  "AI-authored free-form queries must never be executed directly against OpenSearch, SQL engines, shell surfaces, or public-internet search tools."
  "Every hunt request must be expressed as structured query intent rather than raw query text."
  "The gateway must compile validated intent into deterministic query templates owned by AegisOps rather than passing model-authored syntax through to a backend."
  "Validation must reject requests that exceed allowlisted index scope, approved field access, bounded time range, row cap, aggregation policy, or query cost budget."
  '| `Index scope` | Only explicitly allowlisted indices or data views for the approved hunt family may be queried. |'
  '| `Time range` | Every request must carry a bounded start and end time, and the policy must enforce a fixed time cap. |'
  '| `Field access` | Requested filters, projections, sort keys, and grouping fields must come from an allowlist tied to the hunt family. |'
  '| `Row cap` | The gateway must enforce a maximum result window and refuse unbounded result retrieval. |'
  '| `Aggregation` | Aggregations are denied by default and may be enabled only for approved templates with bounded cardinality. |'
  '| `Cost budget` | Each request must stay within a deterministic query-cost budget before execution is attempted. |'
  "Returned observations must carry citations that let an analyst trace each statement back to the underlying index, document identifier or bucket key, and query window used to produce it."
  "A response without sufficient citations must be treated as advisory text only and must not be promoted to evidence, case facts, or approval context."
  '| `Internal-only read` | Approved internal AegisOps data sources such as OpenSearch findings, normalized event stores, or internal case metadata. | No public-internet access and no provider egress beyond the approved internal boundary. |'
  '| `Approved-partner read` | Bounded reads to named external services under contract or delegated trust, such as ticketing, threat intel, or CMDB APIs. | Egress is allowed only to explicitly approved partners with scoped fields, request logging, and ownership. |'
  '| `Public-internet read` | Searches or retrieval against public web content outside approved partner boundaries. | Disabled by default for hunt workflows and must be modeled as a separate trust boundary with explicit approval if ever enabled later. |'
  "Validation failure must return a machine-readable rejection reason that identifies which policy boundary was crossed without silently widening the request."
  "Timeouts, partial backend failures, missing citations, or over-budget results must fail closed rather than returning uncited speculative summaries."
  "This policy preserves the baseline separation between analytics, advisory AI assistance, approval state, and execution surfaces while making data egress risk explicit by trust class."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing safe query gateway document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq "${heading}" "${doc_path}"; then
    echo "Missing safe query gateway heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing safe query gateway statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Safe query gateway document is present and defines bounded intent, deterministic validation, citation-bearing responses, and trust-classed tool policy."
