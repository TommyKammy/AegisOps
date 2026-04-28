#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/roadmap-materialization-preflight-contract.md"
absolute_doc_path="${repo_root}/${doc_path}"

require_file() {
  if [[ ! -s "${absolute_doc_path}" ]]; then
    echo "Missing roadmap materialization preflight contract: ${doc_path}" >&2
    exit 1
  fi
}

require_phrase() {
  local phrase="$1"
  local description="$2"

  if ! grep -Fq -- "${phrase}" "${absolute_doc_path}"; then
    echo "Missing ${description} in ${doc_path}: ${phrase}" >&2
    exit 1
  fi
}

require_file

required_phrases=(
  "Roadmap Materialization Preflight Contract"
  "bash scripts/roadmap-materialization-preflight.sh --graph docs/automation/roadmap-materialization-phase-graph.json --target-phase 49.0 --issue-source github"
  "bash scripts/test-verify-roadmap-materialization-preflight.sh"
  "docs/automation/roadmap-materialization-phase-graph.json"
  "phase_id"
  "epic_issue_number"
  "child_issue_numbers"
  "Part of:"
  "Depends on:"
  "Parallelizable:"
  "Execution order"
  "issue-lint"
  "execution_ready"
  "missing_required"
  "metadata_errors"
  "phase_completion_state"
  "phase_evaluation_state"
  "missing"
  "materialized_open"
  "blocked"
  "execution_ready"
  "merge_or_evaluation_needed"
  "done"
  "pass"
  "fail"
  "phase_classification"
  "invalid_field"
  "suggested_next_safe_action"
  "Phase 49.0/49 must not start before Phase 48, Phase 48.5, Phase 48.6, and Phase 48.7 gates are materialized, lint-clean, and evaluated or explicitly deferred."
  "AegisOps control-plane records remain authoritative workflow truth."
  "tickets, assistant output, ML output, endpoint evidence, network evidence, browser state, receipts, and optional extension status remain subordinate context."
  "Complete phase"
  "Missing child issue"
  "Placeholder dependency"
  "Non-lint-clean issue"
  "node <codex-supervisor-root>/dist/index.js issue-lint <issue-number> --config <supervisor-config-path>"
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${phrase}" "required contract term"
done

echo "Roadmap materialization preflight contract is present and defines required inputs, outputs, classifications, examples, and validation commands."
