#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
preflight="${repo_root}/scripts/roadmap-materialization-preflight.sh"
workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"
graph_path="${workdir}/phase-graph.json"

write_graph() {
  cat >"${graph_path}" <<'EOF'
{
  "snapshot_id": "fixture-phase-48-7",
  "phase_graph_source": "fixture",
  "phases": [
    {
      "phase_id": "48.7",
      "phase_title": "Roadmap Materialization Guard Hardening",
      "phase_status": "done",
      "phase_completion_state": "done",
      "phase_evaluation_state": "evaluated",
      "predecessor_phase_ids": [],
      "epic_issue_number": 911,
      "child_issue_numbers": [912, 913]
    },
    {
      "phase_id": "49.0",
      "phase_title": "Service Class Behavioral Decomposition",
      "phase_status": "planned",
      "phase_completion_state": "not_started",
      "phase_evaluation_state": "not_started",
      "predecessor_phase_ids": ["48.7"]
    }
  ],
  "issues": [
    {
      "number": 911,
      "state": "OPEN",
      "body": "Depends on: none\nParallelizable: No\n\n## Execution order\n1 of 1\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 912,
      "state": "CLOSED",
      "body": "Part of: #911\nDepends on: none\nParallelizable: No\n\n## Execution order\n1 of 2\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 913,
      "state": "CLOSED",
      "body": "Part of: #911\nDepends on: #912\nParallelizable: No\n\n## Execution order\n2 of 2\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    }
  ]
}
EOF
}

assert_passes() {
  if ! bash "${preflight}" --graph "${graph_path}" --target-phase 49.0 --issue-source graph >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected roadmap materialization preflight to pass" >&2
    cat "${pass_stderr}" >&2
    cat "${pass_stdout}" >&2
    exit 1
  fi

  if ! jq -e '.pass == true and .fail == false and .phase_classification["48.7"] == "done" and .invalid_field == null' "${pass_stdout}" >/dev/null; then
    echo "Expected pass output to be machine-readable and classify Phase 48.7 as done" >&2
    cat "${pass_stdout}" >&2
    exit 1
  fi
}

assert_fails_with_json() {
  local jq_filter="$1"
  local description="$2"

  if bash "${preflight}" --graph "${graph_path}" --target-phase 49.0 --issue-source graph >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected roadmap materialization preflight to fail: ${description}" >&2
    exit 1
  fi

  if ! jq -e "${jq_filter}" "${fail_stdout}" >/dev/null; then
    echo "Expected failure output to match ${description}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

write_graph
assert_passes

write_graph
jq 'del(.phases[] | select(.phase_id == "48.7") | .epic_issue_number)' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["48.7"] == "missing" and .invalid_phase_id == "48.7" and .invalid_field == "epic_issue_number"' \
  "missing Epic issue binding"

write_graph
jq 'del(.issues[] | select(.number == 911))' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["48.7"] == "missing" and .invalid_phase_id == "48.7" and .invalid_field == "epic_issue_number" and .invalid_issue_number == 911' \
  "missing bound Epic issue 911"

write_graph
jq '(.issues[] | select(.number == 913) | .body) = "Part of: #911\nDepends on: TBD\nParallelizable: No\n\n## Execution order\n2 of 2\n"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["48.7"] == "blocked" and .invalid_phase_id == "48.7" and .invalid_field == "Depends on:" and .invalid_issue_number == 913' \
  "placeholder Depends on metadata"

write_graph
jq '(.issues[] | select(.number == 913) | .body) = "Part of: #911\nDepends on: #915\nParallelizable: No\n\n## Execution order\n2 of 2\n"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["48.7"] == "blocked" and .invalid_phase_id == "48.7" and .invalid_field == "Depends on:" and .invalid_issue_number == 913' \
  "non-real Depends on issue metadata"

write_graph
jq '(.phases[] | select(.phase_id == "48.7") | .child_issue_numbers) = [912, 913, 914]' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["48.7"] == "missing" and .invalid_phase_id == "48.7" and .invalid_field == "child_issue_numbers" and .invalid_issue_number == 914' \
  "missing child issue 914"

write_graph
jq '(.issues[] | select(.number == 913) | .body) = "Part of: TBD\nDepends on: #912\nParallelizable: No\n\n## Execution order\n2 of 2\n"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["48.7"] == "blocked" and .invalid_phase_id == "48.7" and .invalid_field == "Part of:" and .invalid_issue_number == 913' \
  "placeholder Part of metadata"

write_graph
jq '(.issues[] | select(.number == 913) | .lint.metadata_errors) = "missing-part-of"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["48.7"] == "blocked" and .invalid_phase_id == "48.7" and .invalid_field == "metadata_errors" and .invalid_issue_number == 913' \
  "non-lint-clean issue"

echo "Roadmap materialization preflight tests passed."
