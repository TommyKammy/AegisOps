#!/usr/bin/env bash

set -euo pipefail

source_repo="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

create_fixture_repo() {
  local repo="$1"

  mkdir -p \
    "${repo}/control-plane/tests/fixtures/zammad" \
    "${repo}/docs" \
    "${repo}/scripts"

  cp "${source_repo}/scripts/verify-zammad-live-pilot-boundary.sh" \
    "${repo}/scripts/verify-zammad-live-pilot-boundary.sh"
  cp "${source_repo}/docs/operations-zammad-live-pilot-boundary.md" \
    "${repo}/docs/operations-zammad-live-pilot-boundary.md"
  cp "${source_repo}/control-plane/tests/test_issue812_zammad_live_pilot_boundary_docs.py" \
    "${repo}/control-plane/tests/test_issue812_zammad_live_pilot_boundary_docs.py"
  cp "${source_repo}/control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json" \
    "${repo}/control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json"
}

assert_fails_with() {
  local repo="$1"
  local expected="$2"
  local output

  set +e
  output="$(bash "${repo}/scripts/verify-zammad-live-pilot-boundary.sh" "${repo}" 2>&1)"
  local status=$?
  set -e

  if [[ ${status} -eq 0 ]]; then
    echo "Expected verifier to fail, but it passed." >&2
    exit 1
  fi

  if ! grep -Fq -- "${expected}" <<<"${output}"; then
    echo "Verifier failed with unexpected output." >&2
    echo "Expected: ${expected}" >&2
    echo "Actual:" >&2
    printf '%s\n' "${output}" >&2
    exit 1
  fi
}

fixture_repo="${workdir}/repo"
create_fixture_repo "${fixture_repo}"
bash "${fixture_repo}/scripts/verify-zammad-live-pilot-boundary.sh" "${fixture_repo}"

missing_degraded_repo="${workdir}/missing-degraded"
create_fixture_repo "${missing_degraded_repo}"
perl -0pi -e 's/`degraded`//' "${missing_degraded_repo}/docs/operations-zammad-live-pilot-boundary.md"
assert_fails_with "${missing_degraded_repo}" 'Missing Zammad live pilot boundary statement: `degraded`'

missing_unavailable_repo="${workdir}/missing-unavailable"
create_fixture_repo "${missing_unavailable_repo}"
perl -0pi -e 's/pilot remains unavailable//' "${missing_unavailable_repo}/docs/operations-zammad-live-pilot-boundary.md"
assert_fails_with "${missing_unavailable_repo}" "Missing Zammad live pilot boundary statement: If the reviewed secret source is unavailable, unreadable, empty, stale, or only placeholder-backed, the pilot remains unavailable and fails closed."

missing_rehearsal_fixture_repo="${workdir}/missing-rehearsal-fixture"
create_fixture_repo "${missing_rehearsal_fixture_repo}"
rm "${missing_rehearsal_fixture_repo}/control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json"
assert_fails_with "${missing_rehearsal_fixture_repo}" "Missing Zammad non-authority coordination rehearsal fixture:"

fixture_authority_drift_repo="${workdir}/fixture-authority-drift"
create_fixture_repo "${fixture_authority_drift_repo}"
python3 - "${fixture_authority_drift_repo}/control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
fixture = json.loads(path.read_text(encoding="utf-8"))
fixture["scenarios"][1]["ticket_state_authoritative"] = True
path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
PY
assert_fails_with "${fixture_authority_drift_repo}" "degraded scenario promotes ticket state authority"

authority_drift_repo="${workdir}/authority-drift"
create_fixture_repo "${authority_drift_repo}"
printf '\nZammad is authoritative for closure.\n' >>"${authority_drift_repo}/docs/operations-zammad-live-pilot-boundary.md"
assert_fails_with "${authority_drift_repo}" "Forbidden Zammad live pilot boundary statement: Zammad is authoritative"

placeholder_acceptance_repo="${workdir}/placeholder-acceptance"
create_fixture_repo "${placeholder_acceptance_repo}"
printf '\nplaceholder credentials are valid during bootstrap.\n' >>"${placeholder_acceptance_repo}/docs/operations-zammad-live-pilot-boundary.md"
assert_fails_with "${placeholder_acceptance_repo}" "Forbidden Zammad live pilot boundary statement: placeholder credentials are valid"

echo "Zammad live pilot boundary verifier negative checks passed."
