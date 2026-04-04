#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
template_path="${repo_root}/sigma/aegisops-sigma-metadata-template.yml"

required_phrases=(
  "template_kind: aegisops-sigma-rule-metadata"
  "template_status: placeholder-only"
  "title: AegisOps Sigma Metadata Template"
  "id: <placeholder-uuid>"
  "status: experimental"
  "owner: <team-or-role>"
  "purpose: <what this rule is intended to detect>"
  "expected_behavior: <what analysts should expect when this rule matches>"
  "severity: <low|medium|high|critical>"
  "tags:"
  "  - attack.<tactic-or-technique>"
  "logsource:"
  "  product: <required log source product>"
  "  service: <required log source service or subtype>"
  "field_semantics:"
  "  match_required:"
  "    - <field required for the match logic to retain its intended meaning>"
  "  triage_required:"
  "    - <field required for analysts to investigate a match responsibly>"
  "  activation_gating:"
  "    - <field or prerequisite that must be detection-ready before production activation>"
  "  confidence_degrading:"
  "    - <known gap that does not block staging but reduces confidence or scope>"
  "source_prerequisites:"
  "  - <required log source, retention, field, or normalization dependency>"
  "detection:"
  "  placeholder: metadata-only"
  "  condition: placeholder"
  "activation_policy: metadata-only template; no active Sigma rule logic is introduced from this file"
  "- docs/requirements-baseline.md"
  "- docs/repository-structure-baseline.md"
)

forbidden_patterns=(
  '^status:[[:space:]]*stable$'
  '^status:[[:space:]]*test$'
  '^[[:space:]]*field_dependencies:'
  '^[[:space:]]*selection:'
  '^[[:space:]]*keywords:'
  '^[[:space:]]*CommandLine:'
  '^[[:space:]]*Image:'
)

if [[ ! -f "${template_path}" ]]; then
  echo "Missing Sigma metadata template: ${template_path}" >&2
  exit 1
fi

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${template_path}"; then
    echo "Missing Sigma metadata template field or statement: ${phrase}" >&2
    exit 1
  fi
done

for pattern in "${forbidden_patterns[@]}"; do
  if grep -Eq -- "${pattern}" "${template_path}"; then
    echo "Sigma metadata template must not include real rule logic: ${pattern}" >&2
    exit 1
  fi
done

echo "Sigma metadata template exists, includes required governance fields, and remains placeholder-only."
