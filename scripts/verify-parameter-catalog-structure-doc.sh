#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
doc_path="${repo_root}/docs/parameters/environment-parameter-catalog-structure.md"

required_headings=(
  "## 1. Purpose"
  "## 2. Catalog Locations"
  "## 3. Required Parameter Categories"
  "## 4. Human-Readable and Machine-Readable Split"
  "## 5. Value and Secret Handling Rules"
)

required_phrases=(
  'Human-readable parameter catalog documents must live under `docs/parameters/`.'
  'Machine-readable non-secret parameter files must live under `config/parameters/`.'
  "The initial parameter catalog must define the following categories:"
  '`network`'
  '`compute`'
  '`storage`'
  '`platform`'
  '`security`'
  '`operations`'
  "Human-readable documents describe intent, ownership, and review context."
  "Machine-readable files define non-secret keys, identifiers, defaults, and schema-oriented structure for tooling."
  "This document must not introduce environment-specific secrets, production values, or deployment-time credentials."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing environment parameter catalog structure document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing parameter catalog heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing parameter catalog statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Environment parameter catalog structure document covers the required rules."
