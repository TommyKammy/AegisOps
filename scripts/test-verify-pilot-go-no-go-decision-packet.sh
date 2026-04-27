#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-pilot-go-no-go-decision-packet.sh"
fixture_dir="${repo_root}/docs/deployment/fixtures/pilot-go-no-go-decision-packet"
positive_packet="${repo_root}/docs/deployment/pilot-go-no-go-decision-packet.single-customer-pilot.example.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

assert_passes() {
  local packet="$1"

  if ! bash "${verifier}" --packet "${packet}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${packet}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local packet="$1"
  local expected="$2"

  if bash "${verifier}" --packet "${packet}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${packet}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

assert_passes "${positive_packet}"
assert_fails_with "${fixture_dir}/missing-release-handoff.md" "Missing pilot go/no-go decision packet entry: Release handoff evidence:"
assert_fails_with "${fixture_dir}/mixed-release-identifier.md" "Mixed pilot go/no-go release identifiers:"

workstation_path_packet="${workdir}/workstation-local-path.md"
cp "${fixture_dir}/workstation-local-path.md" "${workstation_path_packet}"
workstation_path="$(printf '/%s/%s/pilot/packet.md' "Users" "example")"
perl -0pi -e "s#__WORKSTATION_LOCAL_PATH__#${workstation_path}#g" "${workstation_path_packet}"
assert_fails_with "${workstation_path_packet}" "Forbidden pilot go/no-go decision packet: workstation-local absolute path detected"

secret_value_packet="${workdir}/secret-looking-value.md"
cp "${fixture_dir}/secret-looking-value.md" "${secret_value_packet}"
secret_value="$(printf '%s=%s' "token" "abc123")"
perl -0pi -e "s#__SECRET_LOOKING_VALUE__#${secret_value}#g" "${secret_value_packet}"
assert_fails_with "${secret_value_packet}" "Secret-looking pilot go/no-go decision packet value detected:"

for required_fixture in \
  missing-detector-activation.md \
  missing-known-limitations.md \
  missing-retention-decision.md \
  missing-zammad-non-authority.md \
  missing-assistant-limitation.md \
  missing-owner.md \
  missing-next-health-review.md; do
  assert_fails_with "${fixture_dir}/${required_fixture}" "Missing pilot go/no-go decision packet entry:"
done

echo "Pilot go/no-go decision packet verifier tests passed."
