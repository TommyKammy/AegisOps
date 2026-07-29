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

fixed_proxy_acl="${workdir}/fixed-proxy-acl"
copy_fixture "${fixed_proxy_acl}"
sed -i.bak 's/allow ${AEGISOPS_LAB_CONTROL_PLANE_IPV4};/allow 172.31.67.20;/' \
  "${fixed_proxy_acl}/control-plane/deployment/phase-67-integration-lab/config/control-plane.conf"
assert_fails_with \
  "${fixed_proxy_acl}" \
  'allow ${AEGISOPS_LAB_CONTROL_PLANE_IPV4};'

unredacted_adapter="${workdir}/unredacted-adapter"
copy_fixture "${unredacted_adapter}"
sed -i.bak 's/api_key: str = field(repr=False)/api_key: str/g' \
  "${unredacted_adapter}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${unredacted_adapter}" \
  'api_key: str = field(repr=False)'

without_terminal_state="${workdir}/without-terminal-state"
copy_fixture "${without_terminal_state}"
sed -i.bak \
  's/payload.get("execution_lifecycle_state") == "succeeded"/payload.get("execution_lifecycle_state") == "failed"/' \
  "${without_terminal_state}/control-plane/deployment/phase-67-integration-lab/shuffle/validate_evidence_manifest.py"
assert_fails_with \
  "${without_terminal_state}" \
  'payload.get("execution_lifecycle_state") == "succeeded"'

without_complete_schema="${workdir}/without-complete-schema"
copy_fixture "${without_complete_schema}"
sed -i.bak \
  '/_validate_schema(payload, schema/d' \
  "${without_complete_schema}/control-plane/deployment/phase-67-integration-lab/shuffle/validate_evidence_manifest.py"
assert_fails_with \
  "${without_complete_schema}" \
  '_validate_schema(payload, schema, "$")'

without_preserved_workflow_check="${workdir}/without-preserved-workflow-check"
copy_fixture "${without_preserved_workflow_check}"
sed -i.bak \
  's/validate_preserved_workflow.py/skip_preserved_workflow.py/' \
  "${without_preserved_workflow_check}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh"
assert_fails_with \
  "${without_preserved_workflow_check}" \
  'validate_preserved_workflow.py'

without_dispatch_recovery="${workdir}/without-dispatch-recovery"
copy_fixture "${without_dispatch_recovery}"
sed -i.bak \
  's/def recover_interrupted_dispatch(/def skip_interrupted_dispatch_recovery(/' \
  "${without_dispatch_recovery}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_dispatch_recovery}" \
  'def recover_interrupted_dispatch('

without_status_normalization="${workdir}/without-status-normalization"
copy_fixture "${without_status_normalization}"
sed -i.bak \
  's/status.strip().lower()/status.lower()/g' \
  "${without_status_normalization}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
assert_fails_with \
  "${without_status_normalization}" \
  'status.strip().lower()'

without_strict_scope_binding="${workdir}/without-strict-scope-binding"
copy_fixture "${without_strict_scope_binding}"
sed -i.bak \
  's/if not _json_values_equal(/if (/g' \
  "${without_strict_scope_binding}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_strict_scope_binding}" \
  'if not _json_values_equal('

without_utc_delegation="${workdir}/without-utc-delegation"
copy_fixture "${without_utc_delegation}"
sed -i.bak \
  's/).astimezone(timezone.utc)/)/' \
  "${without_utc_delegation}/control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py"
assert_fails_with \
  "${without_utc_delegation}" \
  ').astimezone(timezone.utc)'

without_extra_property_rejection="${workdir}/without-extra-property-rejection"
copy_fixture "${without_extra_property_rejection}"
sed -i.bak \
  's/unexpected = sorted(set(observed) - set(expected))/unexpected = []/' \
  "${without_extra_property_rejection}/control-plane/deployment/phase-67-integration-lab/shuffle/validate_preserved_workflow.py"
assert_fails_with \
  "${without_extra_property_rejection}" \
  'unexpected = sorted(set(observed) - set(expected))'

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
