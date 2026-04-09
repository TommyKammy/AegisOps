#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
design_doc="${repo_root}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
guidance_doc="${repo_root}/docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md"
validation_doc="${repo_root}/docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md"
state_model_doc="${repo_root}/docs/control-plane-state-model.md"
runtime_boundary_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"
asset_identity_doc="${repo_root}/docs/asset-identity-privilege-context-baseline.md"
phase14_doc="${repo_root}/docs/phase-14-identity-rich-source-family-design.md"
phase13_doc="${repo_root}/docs/phase-13-guarded-automation-ci-validation.md"
response_safety_doc="${repo_root}/docs/response-action-safety-model.md"
adr_doc="${repo_root}/docs/adr/0002-wazuh-shuffle-control-plane-thesis.md"
phase15_tests="${repo_root}/control-plane/tests/test_phase15_identity_grounded_analyst_assistant_boundary_docs.py"
runtime_tests="${repo_root}/control-plane/tests/test_service_persistence.py"
workflow_path="${repo_root}/.github/workflows/ci.yml"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_string() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required line in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_test_name() {
  local file_path="$1"
  local test_name="$2"

  if ! python3 - "$file_path" "$test_name" <<'PY'
from __future__ import annotations

import ast
import sys
from pathlib import Path


def is_unittest_testcase(base: ast.expr) -> bool:
    if isinstance(base, ast.Attribute):
        return (
            base.attr == "TestCase"
            and isinstance(base.value, ast.Name)
            and base.value.id == "unittest"
        )

    if isinstance(base, ast.Name):
        return base.id == "TestCase"

    return False


file_path = Path(sys.argv[1])
test_name = sys.argv[2]
tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))

for node in tree.body:
    if not isinstance(node, ast.ClassDef):
        continue

    if not any(is_unittest_testcase(base) for base in node.bases):
        continue

    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == test_name:
            raise SystemExit(0)

print(f"Missing required Phase 15 unittest-discoverable test in {file_path}: {test_name}", file=sys.stderr)
raise SystemExit(1)
PY
  then
    exit 1
  fi
}

require_file "${design_doc}" "Missing Phase 15 analyst-assistant boundary design document"
require_file "${guidance_doc}" "Missing Phase 15 analyst-assistant operating guidance document"
require_file "${validation_doc}" "Missing Phase 15 analyst-assistant boundary validation record"
require_file "${state_model_doc}" "Missing control-plane state model"
require_file "${runtime_boundary_doc}" "Missing control-plane runtime service boundary doc"
require_file "${asset_identity_doc}" "Missing asset identity privilege context baseline"
require_file "${phase14_doc}" "Missing Phase 14 identity-rich source family design document"
require_file "${phase13_doc}" "Missing Phase 13 guarded automation validation record"
require_file "${response_safety_doc}" "Missing response action safety model"
require_file "${adr_doc}" "Missing Wazuh and Shuffle control-plane thesis ADR"
require_file "${phase15_tests}" "Missing Phase 15 analyst-assistant boundary tests"
require_file "${runtime_tests}" "Missing Phase 15 assistant response-path runtime tests"
require_file "${workflow_path}" "Missing CI workflow"

require_fixed_string "${workflow_path}" "      - name: Run Phase 15 identity-grounded analyst-assistant boundary validation"
require_fixed_string "${workflow_path}" "      - name: Run Phase 15 workflow coverage guard"

validation_required_phrases=(
  "# Phase 15 Identity-Grounded Analyst-Assistant Boundary Validation"
  "- Validation date: 2026-04-09"
  "- Validation scope: Phase 15 review of the approved analyst-assistant boundary, operator-facing operating guidance, safe-query policy, citation completeness, prompt-injection resistance, identity ambiguity handling, assistant-context snapshot output contracts, optional OpenSearch extension boundaries, advisory-only ceiling, and CI wiring for the reviewed assistant boundary"
  "- Baseline references: \`docs/phase-15-identity-grounded-analyst-assistant-boundary.md\`, \`docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md\`, \`docs/safe-query-gateway-and-tool-policy.md\`, \`docs/phase-7-ai-hunt-design-validation.md\`, \`docs/control-plane-state-model.md\`, \`docs/control-plane-runtime-service-boundary.md\`, \`docs/asset-identity-privilege-context-baseline.md\`, \`docs/phase-14-identity-rich-source-family-design.md\`, \`docs/phase-13-guarded-automation-ci-validation.md\`, \`docs/response-action-safety-model.md\`, \`docs/adr/0002-wazuh-shuffle-control-plane-thesis.md\`, \`control-plane/tests/test_phase15_identity_grounded_analyst_assistant_boundary_docs.py\`, \`control-plane/tests/test_service_persistence.py\`, \`.github/workflows/ci.yml\`"
  "- Verification commands: \`bash scripts/verify-safe-query-gateway-doc.sh\`, \`bash scripts/verify-phase-7-ai-hunt-design-validation.sh\`, \`bash scripts/verify-phase-15-identity-grounded-analyst-assistant-boundary.sh\`, \`python3 -m unittest control-plane.tests.test_phase15_identity_grounded_analyst_assistant_boundary_docs control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_fails_closed_when_identity_context_is_alias_only control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_fails_closed_when_recommendation_text_claims_authority_or_scope_expansion\`, \`bash scripts/test-verify-phase-15-identity-grounded-analyst-assistant-boundary.sh\`, \`bash scripts/test-verify-ci-phase-15-workflow-coverage.sh\`"
  "- Validation status: PASS"
  "## Required Boundary Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  "Confirmed the assistant grounds first on reviewed control-plane records and linked evidence rather than substrate-local summaries or analytics caches."
  "Confirmed the Safe Query Gateway remains the reviewed path for prompt-shaped internal reads and that free-form prompt pressure cannot widen scope, bypass citations, or grant tool authority."
  "Confirmed OpenSearch is only a secondary analyst-assistant extension for optional enrichment and falls back to control-plane-only grounding when absent, stale, incomplete, or conflicting."
  "Confirmed prompt-injection text remains untrusted data, not authority, and citation completeness remains required for every assistant claim."
  "Confirmed identity ambiguity fails closed when only alias-style or otherwise non-stable metadata is available and stable identifiers differ."
  "Confirmed assistant-context snapshot rendering now fails closed on alias-only identity context and on recommendation text that claims approval, execution, reconciliation, or widened scope."
  "Confirmed the assistant remains advisory-only and does not become authority for approval, execution, or reconciliation truth even when optional extension inputs exist."
  "Confirmed the reviewed boundary stays aligned with the Phase 13 approval and execution ceiling, the Phase 14 reviewed-context expansion boundary, and the Phase 7 safe-query and prompt-injection guardrails."
  "Confirmed CI now has a dedicated Phase 15 validation step and workflow coverage guard so boundary drift fails repository-local review."
  "No deviations found."
)

for phrase in "${validation_required_phrases[@]}"; do
  require_fixed_string "${validation_doc}" "${phrase}"
done

required_artifacts=(
  "docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
  "docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md"
  "docs/safe-query-gateway-and-tool-policy.md"
  "docs/phase-7-ai-hunt-design-validation.md"
  "docs/control-plane-state-model.md"
  "docs/control-plane-runtime-service-boundary.md"
  "docs/asset-identity-privilege-context-baseline.md"
  "docs/phase-14-identity-rich-source-family-design.md"
  "docs/phase-13-guarded-automation-ci-validation.md"
  "docs/response-action-safety-model.md"
  "docs/adr/0002-wazuh-shuffle-control-plane-thesis.md"
  "control-plane/tests/test_phase15_identity_grounded_analyst_assistant_boundary_docs.py"
  "control-plane/tests/test_service_persistence.py"
  ".github/workflows/ci.yml"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 15 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 15 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

require_fixed_string "${design_doc}" "# AegisOps Phase 15 Identity-Grounded Analyst-Assistant Boundary"
require_fixed_string "${design_doc}" "This document defines the approved advisory-only analyst-assistant boundary for Phase 15."
require_fixed_string "${design_doc}" "The assistant may treat the following reviewed control-plane record families as first-class grounding inputs:"
require_fixed_string "${design_doc}" "The assistant must prefer the reviewed control-plane record and its linked evidence over any substrate-local raw path, analytics cache entry, or summary row that merely restates the same event."
require_fixed_string "${design_doc}" "OpenSearch may contribute optional analytics or evidence lookups to the assistant path after the reviewed control-plane grounding path exists."
require_fixed_string "${design_doc}" "It is a secondary analyst-assistant extension only: it may enrich reviewed assistance with corroborating analytics, but it must not become a prerequisite for assistance or a replacement for reviewed control-plane grounding."
require_fixed_string "${design_doc}" "OpenSearch does not own alert, case, recommendation, approval, action, or reconciliation truth."
require_fixed_string "${design_doc}" "If OpenSearch is absent, stale, incomplete, or conflicting, the assistant must fall back to control-plane-only grounding and preserve the discrepancy for review rather than treating the OpenSearch result as authoritative."
require_fixed_string "${design_doc}" "The reviewed output layer for Phase 15.1 must render from assistant-context snapshots rather than from free-form assistant text."
require_fixed_string "${design_doc}" "The contract is a narrow structured advisory-output contract for a cited triage summary, case summary, or next-step recommendation draft."
require_fixed_string "${design_doc}" "Every material claim in the contract must anchor to reviewed control-plane records, linked evidence, or reviewed context identifiers."
require_fixed_string "${design_doc}" "The contract keeps the assistant advisory-only and does not allow the output layer to imply approval, execution, or reconciliation authority."
require_fixed_string "${design_doc}" "The cited advisory-output contract must fail-closed."
require_fixed_string "${design_doc}" "If citations are missing, the contract must not render a supported claim and must remain unresolved."
require_fixed_string "${design_doc}" "If reviewed context is conflicting, the contract must surface the conflict in unresolved questions and uncertainty flags rather than silently choosing a side."
require_fixed_string "${design_doc}" "If identity ambiguity cannot be resolved from stable identifiers and reviewed linkage, the contract must not render the entities as the same actor, asset, or accountable subject and must remain unresolved."
require_fixed_string "${design_doc}" "The assistant must fail closed when only alias-style source metadata or otherwise non-stable metadata is available."
require_fixed_string "${design_doc}" "The assistant must not assert equality when the only available evidence is alias-style metadata."
require_fixed_string "${design_doc}" "The assistant is advisory-only."
require_fixed_string "${design_doc}" "It must not become the authority for approval, execution, or reconciliation state."
require_fixed_string "${design_doc}" "The assistant must use the Safe Query Gateway policy for any read-oriented internal lookup that would otherwise rely on free-form search, query expansion, or tool selection outside reviewed control-plane paths."
require_fixed_string "${design_doc}" "Prompt content, analyst notes, and optional-extension instructions are untrusted input."
require_fixed_string "${design_doc}" "The assistant must not use prompt content, analyst text, or optional-extension shortcuts to bypass validation, widen scope, or acquire approval or execution authority."
require_fixed_string "${design_doc}" "The assistant must preserve citation completeness for every advisory claim."
require_fixed_string "${design_doc}" "If a claim cannot be tied back to reviewed records or cited observations, the response must stay advisory-only and unresolved rather than silently widening the answer."
require_fixed_string "${design_doc}" "Optional extension inputs, including OpenSearch analytics, do not override reviewed control-plane truth, stable identifiers, or the citation requirement."
require_fixed_string "${design_doc}" "Alias-style fields may suggest a match, but when stable identifiers differ the assistant must keep the records distinct and report the ambiguity instead of normalizing them into one actor or asset."

require_fixed_string "${guidance_doc}" "# AegisOps Phase 15 Identity-Grounded Analyst-Assistant Operating Guidance"
require_fixed_string "${guidance_doc}" "It is the operator-facing companion to \`docs/phase-15-identity-grounded-analyst-assistant-boundary.md\` and the validation record in \`docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md\`."
require_fixed_string "${guidance_doc}" "The reviewed grounding order is:"
require_fixed_string "${guidance_doc}" "1. reviewed control-plane records and their explicit review state;"
require_fixed_string "${guidance_doc}" "2. linked evidence attached to those records;"
require_fixed_string "${guidance_doc}" "The assistant should not treat an unreviewed substrate-local row, a search hit, or a system-generated summary as equivalent to those reviewed records."
require_fixed_string "${guidance_doc}" "Operators must preserve uncertainty whenever the assistant only has alias-style metadata, heuristic name matches, or other non-stable source labels."
require_fixed_string "${guidance_doc}" "Operators should expect the reviewed output layer to render from assistant-context snapshots rather than from free-form assistant text."
require_fixed_string "${guidance_doc}" "The reviewed advisory output should stay inside a narrow structured advisory-output contract for a cited triage summary, case summary, or next-step recommendation draft."
require_fixed_string "${guidance_doc}" "Each rendered output should include a cited summary, key observations, unresolved questions, candidate recommendations, citations, and uncertainty flags."
require_fixed_string "${guidance_doc}" "If citations are missing, reviewed context is conflicting, or identity ambiguity cannot be resolved from stable identifiers and reviewed linkage, the output should fail-closed and remain unresolved."
require_fixed_string "${guidance_doc}" "OpenSearch must never outrank reviewed control-plane truth, and it does not own alert, case, recommendation, approval, action, or reconciliation state."
require_fixed_string "${guidance_doc}" "The assistant is advisory-only."
require_fixed_string "${guidance_doc}" "Prompt text, analyst notes, and optional-extension hints are untrusted input. They must not be used to bypass validation, widen scope, or obtain approval or execution authority."
require_fixed_string "${guidance_doc}" "This guidance does not define live rollout procedure, marketing language, or environment-specific commands."

require_test_name "${phase15_tests}" "test_phase15_boundary_design_doc_exists"
require_test_name "${phase15_tests}" "test_phase15_operating_guidance_doc_exists"
require_test_name "${phase15_tests}" "test_phase15_operating_guidance_doc_defines_operator_grounding_and_uncertainty_rules"
require_test_name "${phase15_tests}" "test_phase15_validation_doc_exists"
require_test_name "${phase15_tests}" "test_phase15_boundary_design_doc_defines_the_reviewed_grounding_inputs"
require_test_name "${phase15_tests}" "test_phase15_boundary_design_doc_fails_closed_on_ambiguous_identity_metadata"
require_test_name "${phase15_tests}" "test_phase15_boundary_design_doc_defines_safe_query_citation_and_prompt_injection_guardrails"
require_test_name "${phase15_tests}" "test_phase15_boundary_design_doc_defines_cited_advisory_output_contract"
require_test_name "${phase15_tests}" "test_phase15_boundary_design_doc_defines_fail_closed_contract_conditions"
require_test_name "${phase15_tests}" "test_phase15_validation_doc_cross_links_the_boundary_set"
require_test_name "${runtime_tests}" "test_service_fails_closed_when_identity_context_is_alias_only"
require_test_name "${runtime_tests}" "test_service_fails_closed_when_recommendation_text_claims_authority_or_scope_expansion"

echo "Phase 15 identity-grounded analyst-assistant boundary remains reviewable and fail closed."
