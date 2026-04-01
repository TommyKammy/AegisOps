#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/adr/review-path.md"

required_headings=(
  "## 1. Purpose"
  "## 2. When an ADR Is Required"
  "## 3. Proposal Path"
  "## 4. Review Path"
  "## 5. Approval Path"
  "## 6. Supersession Path"
)

required_phrases=(
  "This document defines the ADR lifecycle for AegisOps design changes."
  "It applies to proposal, review, approval, and supersession of ADR-governed changes."
  "An ADR is required before implementation when a change affects architecture, boundaries, naming, security posture, storage layout, or the operating model."
  "Design-change issues and implementation issues must remain separate."
  "An ADR proposal must be created as a dedicated issue or document update before implementation begins."
  "Review must confirm alignment with the current AegisOps requirements baseline and any already accepted ADRs."
  "Approval must be explicit and recorded in the ADR document."
  "Superseding an accepted ADR requires a new ADR that names the older ADR in the supersedes field."
  "This process defines governance only and does not require tool-specific automation."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing ADR review path document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing ADR review path heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing ADR review path statement: ${phrase}" >&2
    exit 1
  fi
done

echo "ADR review path document is present and covers proposal, review, approval, and supersession."
