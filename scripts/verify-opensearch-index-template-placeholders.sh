#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
templates_dir="${repo_root}/opensearch/index-templates"
baseline_doc="${repo_root}/docs/requirements-baseline.md"
naming_guide_doc="${repo_root}/docs/contributor-naming-guide.md"

families=(
  "windows"
  "linux"
  "network"
  "saas"
)

if ! git -C "${repo_root}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a Git working tree: ${repo_root}" >&2
  exit 1
fi

if [[ ! -d "${templates_dir}" ]]; then
  echo "Missing OpenSearch index template directory: ${templates_dir}" >&2
  exit 1
fi

if [[ ! -f "${baseline_doc}" ]]; then
  echo "Missing baseline document: ${baseline_doc}" >&2
  exit 1
fi

if [[ ! -f "${naming_guide_doc}" ]]; then
  echo "Missing contributor naming guide: ${naming_guide_doc}" >&2
  exit 1
fi

for family in "${families[@]}"; do
  pattern="aegisops-logs-${family}-*"
  template_path="${templates_dir}/aegisops-logs-${family}-template.json"

  if ! grep -Fq "${pattern}" "${baseline_doc}"; then
    echo "Baseline is missing approved index naming pattern: ${pattern}" >&2
    exit 1
  fi

  if ! grep -Fq "${pattern}" "${naming_guide_doc}"; then
    echo "Contributor naming guide is missing approved index naming pattern: ${pattern}" >&2
    exit 1
  fi

  if [[ ! -f "${template_path}" ]]; then
    echo "Missing OpenSearch index template placeholder: ${template_path}" >&2
    exit 1
  fi

  if ! grep -Fq "\"${pattern}\"" "${template_path}"; then
    echo "Template placeholder must declare the approved index pattern: ${template_path}" >&2
    exit 1
  fi

  if ! grep -Fq "placeholder only" "${template_path}"; then
    echo "Template placeholder must state that it is a placeholder only: ${template_path}" >&2
    exit 1
  fi

  if grep -Fq '"mappings"' "${template_path}"; then
    echo "Template placeholder must not define production-ready mappings: ${template_path}" >&2
    exit 1
  fi

  if grep -Fq '"index.lifecycle' "${template_path}"; then
    echo "Template placeholder must not define ILM behavior: ${template_path}" >&2
    exit 1
  fi
done

echo "OpenSearch index template placeholders match the approved log-family naming baseline."
