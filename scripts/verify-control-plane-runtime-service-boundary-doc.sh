#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/control-plane-runtime-service-boundary.md"

required_headings=(
  "# AegisOps Control-Plane Runtime Service Boundary"
  "## 1. Purpose"
  "## 2. Approved Runtime Boundary"
  "## 3. Repository Placement and Local Runtime Shape"
  "## 4. Phase 9 Included Capabilities"
  "## 5. Explicit Non-Goals"
  "## 6. System Relationships and Ownership Split"
  "## 7. Alignment Notes"
)

required_phrases=(
  'This document defines the approved runtime boundary and repository placement for the first live AegisOps control-plane service.'
  'This document approves the first live service boundary only. It does not approve an analyst UI, unrestricted runtime expansion, direct response execution, or any new top-level repository area beyond the approved `control-plane/` home described here.'
  'Phase 9 needs a live AegisOps-owned control-plane service that can materialize authoritative platform state without collapsing that authority back into OpenSearch documents or n8n runtime metadata.'
  'The first live control-plane service owns AegisOps-authored application behavior for authoritative control-plane records and reconciliation logic.'
  '`postgres/control-plane/` remains the persistence contract home for reviewed schema and migration assets, but it is not the repository home for live control-plane application code.'
  'The approved repository home for live control-plane application code is the top-level `control-plane/` directory.'
  '- `control-plane/` contains live application code, service bootstrapping, internal APIs, adapters, tests, and service-local documentation for the AegisOps-owned runtime boundary.'
  '- `postgres/control-plane/` contains the reviewed PostgreSQL persistence contract, including schema and migration assets for the AegisOps-owned control-plane datastore boundary.'
  'Language-specific file layout under `control-plane/` may be chosen by the implementation issue, but the runtime must remain rooted there rather than being spread across `opensearch/`, `n8n/`, or `postgres/`.'
  'Included capabilities are:'
  '- a live internal control-plane service rooted under `control-plane/`;'
  '- materialization of authoritative AegisOps control-plane records in the approved PostgreSQL-backed boundary;'
  '- explicit ingestion or synchronization logic for upstream OpenSearch findings or alert-like analytic signals into control-plane-owned records;'
  '- explicit reconciliation logic that can compare control-plane intent with n8n execution outcomes using stable identifiers;'
  '- analyst UI or case-management frontend surfaces;'
  '- live telemetry expansion or source-onboarding growth;'
  '- AI runtime features, prompt execution, or AI-driven workflow authority;'
  '- write-capable response execution or direct replacement of n8n as the execution plane;'
  '- replacing OpenSearch as the analytics and detection plane;'
  'The first live control-plane service sits between OpenSearch and n8n rather than inside either product.'
  '- place live control-plane application code under `postgres/control-plane/`;'
  '- treat OpenSearch documents as the authoritative alert or case record;'
  '- treat n8n execution history as the authoritative approval or action-request record; or'
  '- introduce a second top-level application home for the same control-plane service.'
  '`docs/repository-structure-baseline.md` remains the normative source for approved top-level repository placement, including the dedicated `control-plane/` runtime home and the separate `postgres/control-plane/` persistence contract home.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing control-plane runtime boundary document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing control-plane runtime boundary heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing control-plane runtime boundary statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Control-plane runtime boundary document is present and defines the live service placement and scope boundary."
