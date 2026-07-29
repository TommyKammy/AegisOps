#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-67-3-real-shuffle-transport.sh"
workdir="$(mktemp -d)"
trap 'chmod -R u+w "${workdir}" 2>/dev/null || true; rm -rf "${workdir}"' EXIT

copy_fixture() {
  mkdir -p "$1"
  cp -R "${repo_root}/control-plane" "$1/"
  cp -R "${repo_root}/docs" "$1/"
  cp -R "${repo_root}/postgres" "$1/"
  mkdir -p "$1/scripts"
}

assert_fails_with() {
  if bash "${verifier}" "$1" >"${workdir}/stdout" 2>"${workdir}/stderr"; then
    echo "Expected verifier failure for $1" >&2
    exit 1
  fi
  grep -F -- "$2" "${workdir}/stderr" >/dev/null || {
    cat "${workdir}/stderr" >&2
    exit 1
  }
}

valid="${workdir}/valid"
copy_fixture "${valid}"
bash "${verifier}" "${valid}" >/dev/null

without_tls="${workdir}/without-tls"
copy_fixture "${without_tls}"
sed -i.bak 's/parsed.scheme != "https"/parsed.scheme != "http"/' \
  "${without_tls}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with "${without_tls}" 'parsed.scheme != "https"'

without_replay="${workdir}/without-replay"
copy_fixture "${without_replay}"
sed -i.bak '/reconciliation_id == .replay_reconciliation_id/d' \
  "${without_replay}/control-plane/deployment/phase-67-integration-lab/test-shuffle-execution.sh"
assert_fails_with \
  "${without_replay}" \
  'reconciliation_id == .replay_reconciliation_id'

without_orborus_identity="${workdir}/without-orborus-identity"
copy_fixture "${without_orborus_identity}"
sed -i.bak '/ORBORUS_CONTAINER_NAME:/d' \
  "${without_orborus_identity}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with \
  "${without_orborus_identity}" \
  'ORBORUS_CONTAINER_NAME: ${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:-aegisops-phase67-lab}-shuffle-orborus-1'

synthetic_allowed="${workdir}/synthetic-allowed"
copy_fixture "${synthetic_allowed}"
python3 - \
  "${synthetic_allowed}/control-plane/deployment/phase-67-integration-lab/shuffle/evidence-manifest.schema.json" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
schema = json.loads(path.read_text(encoding="utf-8"))
schema["properties"]["execution_id"].pop("not")
path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
PY
assert_fails_with "${synthetic_allowed}" '"pattern": "^shuffle-run-"'

inline_secret="${workdir}/inline-secret"
copy_fixture "${inline_secret}"
printf '\n# Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456\n' \
  >>"${inline_secret}/control-plane/deployment/phase-67-integration-lab/shuffle/run_real_trial.py"
assert_fails_with \
  "${inline_secret}" \
  "Committed Phase 67.3 artifact contains an inline API credential"

echo "PASS: Phase 67.3 verifier self-tests passed."
