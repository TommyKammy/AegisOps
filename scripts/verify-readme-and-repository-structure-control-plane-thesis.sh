#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
readme_path="${repo_root}/README.md"
structure_doc="${repo_root}/docs/repository-structure-baseline.md"

readme_required_phrases=(
  "**AegisOps** is a governed SecOps control plane above external detection and automation substrates."
  "Current scope:"
  "- Platform baseline definition"
  "- Architecture design and operating guidance"
  "- Repository scaffolding"
  "- Parameter catalog structure"
  "- Implementation guardrails for AI-assisted development"
  "- **OpenSearch** — optional or transitional analytics substrate, not the product core"
  "- **Sigma** — optional or transitional rule-definition format or translation source, not the product core"
  "- **n8n** — optional, transitional, or experimental orchestration substrate, not the product core"
  "- **Control Plane Runtime** — future authoritative AegisOps service boundary for platform state and reconciliation"
  "OpenSearch, Sigma, and n8n remain repository-tracked assets, but they are subordinate to the approved control-plane thesis and must not redefine the product narrative around themselves."
  "The current top-level tree still includes older substrate-specific directories and should be treated as transitional until a later ADR approves any substrate-specific repository rebaseline."
)

readme_forbidden_phrases=(
  "**AegisOps** is an internal SOC + SOAR platform blueprint designed for flexible deployment across on-premise infrastructure and cloud environments, including AWS and other providers."
  "- **OpenSearch** — SIEM analytics and detection"
  "- **Sigma** — curated, reviewable detection logic"
  "- **n8n** — approval-gated orchestration, enrichment, and response"
)

structure_required_phrases=(
  "This document intentionally defines the approved top-level repository layout and the purpose of each entry."
  "The current top-level structure remains transitional because it still reflects earlier repository phases and substrate-specific directory ownership."
  "Until a later ADR approves a repository rebaseline, contributors must treat the existing top-level tree as the reviewed baseline even where it does not yet match the long-term control-plane thesis."
  "| \`opensearch/\` | Transitional or optional OpenSearch repository assets such as compose definitions, detectors, templates, ILM policies, and snapshot-related configuration. Their presence does not make OpenSearch the product core. |"
  "| \`sigma/\` | Transitional or optional Sigma repository assets, including reviewed rules, curated subsets, suppressions, field mappings, and placeholder markers that keep approved onboarding paths explicit before real rule content is added. Their presence does not make Sigma the product core. |"
  "| \`n8n/\` | Transitional, optional, or experimental n8n workflow assets, approval patterns, credential templates, and webhook contract definitions. Their presence does not make n8n the product core or authority surface. |"
  "| \`control-plane/\` | Live AegisOps control-plane application code, service bootstrapping, adapters, tests, and service-local documentation for the approved runtime boundary. |"
  "- This document defines structure only and does not authorize runtime, deployment, or workflow implementation."
)

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README document: ${readme_path}" >&2
  exit 1
fi

if [[ ! -f "${structure_doc}" ]]; then
  echo "Missing repository structure baseline document: ${structure_doc}" >&2
  exit 1
fi

for phrase in "${readme_required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${readme_path}"; then
    echo "Missing README control-plane thesis statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${readme_forbidden_phrases[@]}"; do
  if grep -Fq -- "${phrase}" "${readme_path}"; then
    echo "Forbidden legacy README statement present: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${structure_required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${structure_doc}"; then
    echo "Missing repository structure thesis statement: ${phrase}" >&2
    exit 1
  fi
done

echo "README and repository structure baseline reflect the governed control-plane thesis."
