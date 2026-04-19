#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-}"
if [[ "${repo_root}" == "--print" ]]; then
  print_only=1
  mode="${2:?missing mode}"
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
else
  print_only=0
  mode="${1:?missing mode}"
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

. "${repo_root}/scripts/ci-phase-contract-commands.sh"

case "${mode}" in
  all-verifiers)
    commands="$(phase_contract_all_verifier_commands)"
    ;;
  all-shell-tests)
    commands="$(phase_contract_all_shell_test_commands)"
    ;;
  *)
    echo "Unsupported phase-contract mode: ${mode}" >&2
    exit 1
    ;;
esac

if [[ "${print_only}" -eq 1 ]]; then
  printf '%s\n' "${commands}"
  exit 0
fi

cd "${repo_root}"
while IFS= read -r command; do
  [[ -z "${command}" ]] && continue
  printf '%s\n' "${command}"
  bash -lc "${command}"
done <<<"${commands}"
