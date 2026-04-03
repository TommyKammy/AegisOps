#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
doc_path="${repo_root}/n8n/workflows/README.md"

required_headings=(
  "## 1. Purpose"
  "## 2. Approved Workflow Categories"
  "## 3. Placeholder Boundary"
  "## 4. Control vs Execution Alignment"
  "## 5. Contributor Guidance"
  "## 6. Reference Documents"
)

required_phrases=(
  "This directory exists to document the approved workflow-category boundaries for AegisOps n8n assets."
  "The approved workflow categories are alert ingest, enrich, approve, notify, and response."
  'Placeholder directories and marker files under `n8n/workflows/` remain non-production placeholders for categories that do not yet contain an explicitly approved exported workflow asset.'
  "OpenSearch remains responsible for detection and analytics, while n8n is limited to approved orchestration, enrichment, approval handling, notification routing, and controlled downstream execution."
  'The approved Phase 6 exception is limited to `aegisops_enrich_windows_selected_detector_outputs.json` and `aegisops_notify_windows_selected_detector_outputs.json`.'
  "The approved Phase 6 workflow assets must remain read-only for enrichment and notify-only for analyst routing, without response execution, write-capable connectors, or uncontrolled downstream mutation."
  "Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline beyond the current Phase 6 read-only workflow assets."
)

required_references=(
  '`docs/architecture.md`'
  '`docs/requirements-baseline.md`'
  '`docs/repository-structure-baseline.md`'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing n8n workflow category guidance document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing n8n workflow category guidance heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing n8n workflow category guidance statement: ${phrase}" >&2
    exit 1
  fi
done

for reference in "${required_references[@]}"; do
  if ! grep -Fq "${reference}" "${doc_path}"; then
    echo "Missing n8n workflow category guidance reference: ${reference}" >&2
    exit 1
  fi
done

echo "n8n workflow category guidance documents approved categories, the limited Phase 6 workflow exception, and control-versus-execution boundaries."
