#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/architecture.md"

required_headings=(
  "## 1. Purpose"
  "## 2. Architecture Overview"
  "## 3. Component Responsibilities and Boundaries"
  "## 4. Control Plane vs Execution Plane"
  "## 5. Approved Access Model"
  "## 6. Baseline Alignment Notes"
)

required_phrases=(
  "This document summarizes the approved baseline architecture for AegisOps."
  "This document describes the approved baseline only and does not introduce runtime changes."
  "OpenSearch is the SIEM core for log ingestion, storage, search, analytics, and detection."
  "Sigma defines detection logic only and is not a runtime execution engine."
  "n8n handles enrichment, routing, orchestration, approval workflows, and downstream integration."
  "PostgreSQL stores n8n metadata and execution state."
  "Redis is reserved for optional future workflow queueing and future scaling."
  "The proxy provides TLS termination and controlled user-facing access."
  "The ingest role handles syslog, API-based, and agent-based collection and parsing before data reaches analytics systems."
  "Detection and execution remain strictly separated in the approved baseline."
  "OpenSearch performs detection and analytics only and must not directly execute response actions."
  "n8n may execute approved workflows only after validation and approval requirements are satisfied."
  "All external UI access must traverse the approved reverse proxy."
  "Direct unaudited exposure of internal service ports is not part of the approved baseline."
  "This overview reflects the current approved baseline and must not be used to infer unapproved architecture changes."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing architecture overview document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing architecture heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing architecture statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Architecture overview document is present and covers the approved baseline roles and boundaries."
