#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/documentation-ownership-map.md"

required_headings=(
  "# AegisOps Documentation Ownership Map"
  "## 1. Purpose"
  "## 2. Ownership Terms"
  "## 3. Ownership Map"
)

required_phrases=(
  "This document records the default ownership map for major AegisOps documentation areas in one place."
  "It supplements existing document-control metadata and does not replace per-document owner fields where those fields already exist."
  "Document owner means the team accountable for keeping the document area current, reviewable, and aligned with the approved baseline and accepted ADRs."
  '| `docs/requirements-baseline.md` | Requirements baseline | IT Operations, Information Systems Department |'
  '| `docs/adr/` | Architecture Decision Records (ADRs) | IT Operations, Information Systems Department |'
  '| `docs/parameters/` | Parameter documentation | IT Operations, Information Systems Department |'
  '| `docs/runbook.md` | Runbooks | IT Operations, Information Systems Department |'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing documentation ownership map: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing ownership map heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing ownership map statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Documentation ownership map exists and defines owners for the required documentation areas."
