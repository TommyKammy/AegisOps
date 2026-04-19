#!/usr/bin/env bash

expand_phase_contract_helper_commands() {
  local raw_commands="${1}"

  while IFS= read -r command; do
    case "${command}" in
      "bash scripts/run-ci-phase-contract.sh all-verifiers")
        "${repo_root}/scripts/run-ci-phase-contract.sh" --print all-verifiers
        ;;
      "bash scripts/run-ci-phase-contract.sh all-shell-tests")
        "${repo_root}/scripts/run-ci-phase-contract.sh" --print all-shell-tests
        ;;
      *)
        printf '%s\n' "${command}"
        ;;
    esac
  done <<<"${raw_commands}"
}

collect_active_run_commands() {
  local raw_commands
  raw_commands="$(
    awk '
      {
        if (in_block) {
          if ($0 ~ /^[[:space:]]*$/) {
            next
          }

          current_indent = match($0, /[^ ]/) - 1
          if (current_indent > block_indent) {
            line = $0
            sub(/^[[:space:]]+/, "", line)
            if (line != "" && line !~ /^#/) {
              print line
            }
            next
          }

          in_block = 0
        }

        if ($0 ~ /^[[:space:]]*run:[[:space:]]*[|>]-?[[:space:]]*$/) {
          block_indent = match($0, /[^ ]/) - 1
          in_block = 1
          next
        }

        if ($0 ~ /^[[:space:]]*run:[[:space:]]*[^|>]/) {
          line = $0
          sub(/^[[:space:]]*run:[[:space:]]*/, "", line)
          if (line != "" && line !~ /^#/) {
            print line
          }
        }
      }
    ' "${workflow_path}"
  )"

  expand_phase_contract_helper_commands "${raw_commands}"
}

extract_step_run_commands() {
  local step_name="${1}"

  local raw_commands
  raw_commands="$(
    awk -v step_name="${step_name}" '
    function line_indent(line) {
      return match(line, /[^ ]/) - 1
    }

    BEGIN {
      in_step = 0
      step_indent = -1
      in_block = 0
      block_indent = -1
    }

    {
      if (in_step) {
        if ($0 ~ /^[[:space:]]*-[[:space:]]name:[[:space:]]+/ && line_indent($0) <= step_indent) {
          exit 0
        }

        if (in_block) {
          if ($0 ~ /^[[:space:]]*$/) {
            next
          }

          current_indent = line_indent($0)
          if (current_indent > block_indent) {
            line = $0
            sub(/^[[:space:]]+/, "", line)
            if (line != "" && line !~ /^#/) {
              print line
            }
            next
          }

          in_block = 0
        }

        if ($0 ~ /^[[:space:]]*run:[[:space:]]*[|>]-?[[:space:]]*$/) {
          block_indent = line_indent($0)
          in_block = 1
          next
        }

        if ($0 ~ /^[[:space:]]*run:[[:space:]]*/) {
          line = $0
          sub(/^[[:space:]]*run:[[:space:]]*/, "", line)
          if (line != "" && line !~ /^#/) {
            print line
          }
          next
        }
      }

      line = $0
      sub(/^[[:space:]]+/, "", line)
      if (line == "- name: " step_name) {
        in_step = 1
        step_indent = line_indent($0)
      }
    }
    ' "${workflow_path}"
  )"

  expand_phase_contract_helper_commands "${raw_commands}"
}
