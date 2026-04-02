#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
doc_path="${repo_root}/sigma/README.md"

required_headings=(
  "## Purpose"
  "## Directory Roles"
  '### `curated/`'
  '### `suppressed/`'
  "## Review Expectations"
  "## Validation Expectations"
  "## Scope Boundary"
)

required_markers=(
  "reviewed Sigma rules that are approved for future AegisOps onboarding"
  "documented suppression decisions for Sigma content that should remain excluded from onboarding"
  'A rule belongs in `curated/` when it has passed content review and is retained as an approved candidate for future platform onboarding.'
  'An entry belongs in `suppressed/` when the decision to exclude or defer Sigma content must be preserved with documented rationale, review, and approval context.'
  "Any future addition under either directory must remain reviewable, attributable, and explicitly approved before placeholder-only status is removed."
  "Contributors must validate that directory purpose, review state, and supporting documentation remain clear before merging changes."
  "This document defines repository content governance only. It does not activate detections, create suppression behavior, or change runtime execution in OpenSearch, Sigma tooling, or n8n."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Sigma guidance document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing heading in Sigma guidance document: ${heading}" >&2
    exit 1
  fi
done

for marker in "${required_markers[@]}"; do
  if ! grep -Fq "${marker}" "${doc_path}"; then
    echo "Missing required Sigma guidance text: ${marker}" >&2
    exit 1
  fi
done

if ! grep -Fq "docs/requirements-baseline.md" "${doc_path}"; then
  echo "Sigma guidance document must cite docs/requirements-baseline.md as the baseline source." >&2
  exit 1
fi

echo "Sigma guidance document is present and covers curated content governance."
