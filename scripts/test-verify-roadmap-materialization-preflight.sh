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
target_phase="49.0"
expected_done_phase="48.7"

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
      "state": "CLOSED",
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
  if ! bash "${preflight}" --graph "${graph_path}" --target-phase "${target_phase}" --issue-source graph >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected roadmap materialization preflight to pass" >&2
    cat "${pass_stderr}" >&2
    cat "${pass_stdout}" >&2
    exit 1
  fi

  if ! jq -e --arg phase "${expected_done_phase}" '.pass == true and .fail == false and .phase_classification[$phase] == "done" and .invalid_field == null' "${pass_stdout}" >/dev/null; then
    echo "Expected pass output to be machine-readable and classify Phase ${expected_done_phase} as done" >&2
    cat "${pass_stdout}" >&2
    exit 1
  fi
}

assert_fails_with_json() {
  local jq_filter="$1"
  local description="$2"

  if bash "${preflight}" --graph "${graph_path}" --target-phase "${target_phase}" --issue-source graph >"${fail_stdout}" 2>"${fail_stderr}"; then
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

write_graph
jq '(.issues[] | select(.number == 913) | .state) = "OPEN"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["48.7"] == "materialized_open" and .invalid_phase_id == "48.7" and .invalid_field == "issue_state" and .invalid_issue_number == 913' \
  "open predecessor child issue"

write_phase51_graph() {
  target_phase="52"
  expected_done_phase="51"
  cat >"${graph_path}" <<'EOF'
{
  "snapshot_id": "fixture-phase-51-post-phase50",
  "phase_graph_source": "fixture",
  "target_phase_ids": ["52"],
  "phases": [
    {
      "phase_id": "51",
      "phase_title": "Replacement Thesis, Gates, Boundary ADR",
      "phase_status": "done",
      "phase_completion_state": "done",
      "phase_evaluation_state": "evaluated",
      "predecessor_phase_ids": [],
      "epic_issue_number": 1041,
      "child_issue_numbers": [1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049]
    },
    {
      "phase_id": "52",
      "phase_title": "Setup and Guided Onboarding",
      "phase_status": "planned",
      "phase_completion_state": "not_started",
      "phase_evaluation_state": "not_started",
      "predecessor_phase_ids": ["51"]
    }
  ],
  "issues": [
    {
      "number": 1041,
      "state": "CLOSED",
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
      "number": 1042,
      "state": "CLOSED",
      "body": "Part of: #1041\nDepends on: none\nParallelizable: No\n\n## Execution order\n1 of 8\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 1043,
      "state": "CLOSED",
      "body": "Part of: #1041\nDepends on: #1042\nParallelizable: Yes\n\n## Execution order\n2 of 8\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 1044,
      "state": "CLOSED",
      "body": "Part of: #1041\nDepends on: #1042\nParallelizable: Yes\n\n## Execution order\n3 of 8\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 1045,
      "state": "CLOSED",
      "body": "Part of: #1041\nDepends on: #1042\nParallelizable: Yes\n\n## Execution order\n4 of 8\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 1046,
      "state": "CLOSED",
      "body": "Part of: #1041\nDepends on: #1042\nParallelizable: Yes\n\n## Execution order\n5 of 8\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 1047,
      "state": "CLOSED",
      "body": "Part of: #1041\nDepends on: #1042\nParallelizable: No\n\n## Execution order\n6 of 8\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 1048,
      "state": "CLOSED",
      "body": "Part of: #1041\nDepends on: #1044\nParallelizable: Yes\n\n## Execution order\n7 of 8\n",
      "lint": {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none"
      }
    },
    {
      "number": 1049,
      "state": "CLOSED",
      "body": "Part of: #1041\nDepends on: #1043, #1044, #1045, #1046, #1047, #1048\nParallelizable: No\n\n## Execution order\n8 of 8\n",
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

write_phase51_graph
assert_passes

write_phase51_graph
jq 'del(.phases[] | select(.phase_id == "51") | .epic_issue_number)' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["51"] == "missing" and .invalid_phase_id == "51" and .invalid_field == "epic_issue_number"' \
  "missing Phase 51 Epic binding"

write_phase51_graph
jq 'del(.issues[] | select(.number == 1049))' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["51"] == "missing" and .invalid_phase_id == "51" and .invalid_field == "child_issue_numbers" and .invalid_issue_number == 1049' \
  "missing Phase 51 child issue"

write_phase51_graph
jq '(.issues[] | select(.number == 1048) | .body) = "Depends on: #1044\nParallelizable: Yes\n\n## Execution order\n7 of 8\n"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["51"] == "blocked" and .invalid_phase_id == "51" and .invalid_field == "Part of:" and .invalid_issue_number == 1048' \
  "missing Phase 51 Part of metadata"

write_phase51_graph
jq '(.issues[] | select(.number == 1048) | .body) = "Part of: #1041\nParallelizable: Yes\n\n## Execution order\n7 of 8\n"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["51"] == "blocked" and .invalid_phase_id == "51" and .invalid_field == "Depends on:" and .invalid_issue_number == 1048' \
  "missing Phase 51 Depends on metadata"

write_phase51_graph
jq '(.issues[] | select(.number == 1048) | .body) = "Part of: #1041\nDepends on: #1044\nParallelizable: Yes\n"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["51"] == "blocked" and .invalid_phase_id == "51" and .invalid_field == "Execution order" and .invalid_issue_number == 1048' \
  "missing Phase 51 execution order"

write_phase51_graph
jq '(.issues[] | select(.number == 1048) | .lint.execution_ready) = "no"' "${graph_path}" >"${graph_path}.tmp"
mv "${graph_path}.tmp" "${graph_path}"
assert_fails_with_json \
  '.pass == false and .fail == true and .phase_classification["51"] == "blocked" and .invalid_phase_id == "51" and .invalid_field == "execution_ready" and .invalid_issue_number == 1048' \
  "not-lint-clean Phase 51 issue set"

echo "Roadmap materialization preflight tests passed."
