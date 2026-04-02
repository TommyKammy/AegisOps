#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
template_path="${repo_root}/opensearch/detectors/aegisops-detector-metadata-template.yaml"

required_phrases=(
  "template_kind: aegisops-detector-metadata"
  "template_status: placeholder-only"
  "detector_name: aegisops-<source>-<use-case>-<severity>"
  "owner: <team-or-role>"
  "purpose: <what this detector is intended to identify>"
  "severity: <low|medium|high|critical>"
  "expected_behavior: <what analysts should expect when this detector matches>"
  "source_prerequisites:"
  "  - <required log source, index pattern, or field dependency>"
  "activation_policy: metadata-only template; no active detector is introduced from this file"
  "- docs/requirements-baseline.md"
  "- docs/contributor-naming-guide.md"
  "- docs/repository-structure-baseline.md"
)

forbidden_patterns=(
  '^enabled:[[:space:]]*true$'
  '^enabled:[[:space:]]*false$'
  '^triggers:[[:space:]]*$'
  '^inputs:[[:space:]]*$'
  '^schedule:[[:space:]]*$'
)

if [[ ! -f "${template_path}" ]]; then
  echo "Missing OpenSearch detector metadata template: ${template_path}" >&2
  exit 1
fi

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${template_path}"; then
    echo "Missing detector metadata template field or statement: ${phrase}" >&2
    exit 1
  fi
done

for pattern in "${forbidden_patterns[@]}"; do
  if grep -Eq -- "${pattern}" "${template_path}"; then
    echo "Detector metadata template must not include runnable detector content: ${pattern}" >&2
    exit 1
  fi
done

echo "OpenSearch detector metadata template exists, includes required governance fields, and remains non-runnable."
