#!/usr/bin/env bash

set -euo pipefail
umask 077
trap 'rc=$?; echo "BLOCKED: Wazuh intake trial failed at line ${LINENO} (exit ${rc})" >&2' ERR

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${LAB_DIR}/../../.." && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_environment
require_command curl
require_command git
require_command jq
require_command python3

fixture="${REPO_ROOT}/control-plane/tests/fixtures/wazuh/phase53-smb-single-node-ssh-auth-failure-alert.json"
[[ -s "${fixture}" ]] || fail "reviewed Wazuh negative-test fixture is missing"
shared_secret_file="${AEGISOPS_LAB_SECRET_DIR}/wazuh-ingest-shared-secret"
[[ -s "${shared_secret_file}" ]] || fail "Wazuh intake shared secret is missing"
shared_secret="$(<"${shared_secret_file}")"
proxy_url="https://localhost:${AEGISOPS_LAB_PROXY_PORT}/intake/wazuh"
proxy_ca="${AEGISOPS_LAB_PROXY_CERT_DIR}/lab.crt"
[[ -s "${proxy_ca}" ]] || fail "Phase 67 proxy CA is missing"

running_services="$(compose_scope wazuh ps --services --status running)"
for required_service in control-plane proxy wazuh-manager; do
  grep -Fqx "${required_service}" <<<"${running_services}" \
    || fail "${required_service} is not running; run ${LAB_DIR}/up.sh wazuh"
done

manager_status="$(
  compose_scope wazuh exec -T wazuh-manager \
    /var/ossec/bin/wazuh-control status || true
)"
grep -Fq "wazuh-analysisd is running" <<<"${manager_status}" \
  || fail "Wazuh analysisd is not healthy"
grep -Fq "wazuh-integratord is running" <<<"${manager_status}" \
  || fail "Wazuh integratord is not healthy"

temporary_dir="$(mktemp -d "${TMPDIR:-/tmp}/aegisops-phase67-wazuh.XXXXXX")"
cleanup() {
  rm -rf "${temporary_dir}"
}
trap cleanup EXIT
authenticated_header_file="${temporary_dir}/authenticated-header"
invalid_header_file="${temporary_dir}/invalid-header"
printf 'Authorization: Bearer %s\n' "${shared_secret}" >"${authenticated_header_file}"
printf 'Authorization: Bearer invalid-phase67-secret\n' >"${invalid_header_file}"
chmod 600 "${authenticated_header_file}" "${invalid_header_file}"
unset shared_secret

http_status() {
  local output_file="$1"
  shift

  curl \
    --silent \
    --show-error \
    --output "${output_file}" \
    --write-out "%{http_code}" \
    --cacert "${proxy_ca}" \
    "$@"
}

analyst_queue_count() {
  compose_scope wazuh exec -T control-plane \
    python3 main.py inspect-analyst-queue \
    | jq -er '
        .total_records
        | if type == "number" and . >= 0 and floor == .
          then .
          else error("invalid analyst queue count")
          end
      '
}

tree_digest() {
  local root="$1"
  local manifest="$2"

  python3 - "${root}" "${manifest}" <<'PY'
from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1])
paths = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
digest = hashlib.sha256()
for relative_path in sorted(paths):
    path = root / relative_path
    if not path.is_file():
        raise SystemExit(f"runtime artifact is missing: {path}")
    digest.update(relative_path.encode("utf-8"))
    digest.update(b"\0")
    digest.update(path.read_bytes())
    digest.update(b"\0")
print(digest.hexdigest())
PY
}

runtime_tree_digest() {
  local service="$1"
  local root="$2"
  local manifest="$3"

  compose_scope wazuh exec -T "${service}" \
    python3 -c '
from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1])
paths = sys.stdin.read().splitlines()
digest = hashlib.sha256()
for relative_path in sorted(paths):
    path = root / relative_path
    if not path.is_file():
        raise SystemExit(f"runtime artifact is missing: {path}")
    digest.update(relative_path.encode("utf-8"))
    digest.update(b"\0")
    digest.update(path.read_bytes())
    digest.update(b"\0")
print(digest.hexdigest())
' "${root}" <"${manifest}"
}

file_digest() {
  python3 - "$1" <<'PY'
from pathlib import Path
import hashlib
import sys

print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
PY
}

runtime_file_digest() {
  local service="$1"
  local path="$2"

  compose_scope wazuh exec -T "${service}" \
    python3 -c '
from pathlib import Path
import hashlib
import sys

print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
' "${path}"
}

aggregate_artifact_digest() {
  python3 - "$@" <<'PY'
import hashlib
import sys

digest = hashlib.sha256()
for component in sys.argv[1:]:
    digest.update(component.encode("ascii"))
    digest.update(b"\0")
print(digest.hexdigest())
PY
}

control_plane_manifest="${temporary_dir}/control-plane-artifacts"
migrations_manifest="${temporary_dir}/postgres-migration-artifacts"
write_artifact_manifests() {
  git -C "${REPO_ROOT}" ls-files --cached --others --exclude-standard \
    -- control-plane \
    | sed 's#^control-plane/##' >"${control_plane_manifest}"
  git -C "${REPO_ROOT}" ls-files --cached --others --exclude-standard \
    -- postgres/control-plane/migrations \
    | sed 's#^postgres/control-plane/migrations/##' >"${migrations_manifest}"
  [[ -s "${control_plane_manifest}" && -s "${migrations_manifest}" ]] \
    || fail "could not inventory Phase 67 runtime artifacts"
}

capture_artifact_digests() {
  local worktree_control_plane
  local runtime_control_plane
  local worktree_migrations
  local runtime_migrations
  local worktree_wrapper
  local runtime_wrapper
  local worktree_integrator
  local runtime_integrator

  worktree_control_plane="$(
    tree_digest "${REPO_ROOT}/control-plane" "${control_plane_manifest}"
  )"
  runtime_control_plane="$(
    runtime_tree_digest \
      control-plane \
      /opt/aegisops/control-plane \
      "${control_plane_manifest}"
  )"
  worktree_migrations="$(
    tree_digest \
      "${REPO_ROOT}/postgres/control-plane/migrations" \
      "${migrations_manifest}"
  )"
  runtime_migrations="$(
    runtime_tree_digest \
      control-plane \
      /opt/aegisops/postgres-migrations \
      "${migrations_manifest}"
  )"
  worktree_wrapper="$(
    file_digest "${LAB_DIR}/wazuh/custom-aegisops"
  )"
  runtime_wrapper="$(
    runtime_file_digest wazuh-manager /var/ossec/integrations/custom-aegisops
  )"
  worktree_integrator="$(
    file_digest "${LAB_DIR}/wazuh/aegisops_wazuh_integrator.py"
  )"
  runtime_integrator="$(
    runtime_file_digest \
      wazuh-manager \
      /var/ossec/integrations/aegisops_wazuh_integrator.py
  )"

  worktree_artifact_digest="$(
    aggregate_artifact_digest \
      "control-plane=${worktree_control_plane}" \
      "postgres-migrations=${worktree_migrations}" \
      "wazuh-wrapper=${worktree_wrapper}" \
      "wazuh-integrator=${worktree_integrator}"
  )"
  runtime_artifact_digest="$(
    aggregate_artifact_digest \
      "control-plane=${runtime_control_plane}" \
      "postgres-migrations=${runtime_migrations}" \
      "wazuh-wrapper=${runtime_wrapper}" \
      "wazuh-integrator=${runtime_integrator}"
  )"
  [[ "${runtime_artifact_digest}" == "${worktree_artifact_digest}" ]] \
    || fail "running Phase 67 artifacts do not match the worktree; run ${LAB_DIR}/up.sh wazuh"
}

repository_revision="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
write_artifact_manifests
capture_artifact_digests
initial_artifact_digest="${worktree_artifact_digest}"

negative_baseline_alert_count="$(analyst_queue_count)"

missing_secret_status="$(
  http_status "${temporary_dir}/missing-secret.json" \
    --header "Content-Type: application/json" \
    --data-binary "@${fixture}" \
    "${proxy_url}"
)"
[[ "${missing_secret_status}" == "403" ]] \
  || fail "missing Bearer secret must return HTTP 403, got ${missing_secret_status}"

invalid_secret_status="$(
  http_status "${temporary_dir}/invalid-secret.json" \
    --header "@${invalid_header_file}" \
    --header "Content-Type: application/json" \
    --data-binary "@${fixture}" \
    "${proxy_url}"
)"
[[ "${invalid_secret_status}" == "403" ]] \
  || fail "invalid Bearer secret must return HTTP 403, got ${invalid_secret_status}"

malformed_status="$(
  http_status "${temporary_dir}/malformed.json" \
    --header "@${authenticated_header_file}" \
    --header "Content-Type: application/json" \
    --data-binary '{"broken":' \
    "${proxy_url}"
)"
[[ "${malformed_status}" == "400" ]] \
  || fail "malformed JSON must return HTTP 400, got ${malformed_status}"

jq '.data.source_family = "unsupported_phase67_source"' \
  "${fixture}" >"${temporary_dir}/unsupported.json"
unsupported_status="$(
  http_status "${temporary_dir}/unsupported-response.json" \
    --header "@${authenticated_header_file}" \
    --header "Content-Type: application/json" \
    --data-binary "@${temporary_dir}/unsupported.json" \
    "${proxy_url}"
)"
[[ "${unsupported_status}" == "400" ]] \
  || fail "unsupported source family must return HTTP 400, got ${unsupported_status}"

python3 - "${temporary_dir}/oversized.json" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_bytes(b"x" * (256 * 1024 + 1))
PY
oversized_status="$(
  http_status "${temporary_dir}/oversized-response.json" \
    --header "@${authenticated_header_file}" \
    --header "Content-Type: application/json" \
    --data-binary "@${temporary_dir}/oversized.json" \
    "${proxy_url}"
)"
[[ "${oversized_status}" == "413" ]] \
  || fail "oversized payload must return HTTP 413, got ${oversized_status}"

set +e
http_probe_status="$(
  curl \
    --silent \
    --show-error \
    --output /dev/null \
    --write-out "%{http_code}" \
    --max-time 5 \
    "http://127.0.0.1:${AEGISOPS_LAB_PROXY_PORT}/intake/wazuh" 2>/dev/null
)"
http_probe_rc=$?
set -e
[[ "${http_probe_rc}" -ne 0 || "${http_probe_status}" != "202" ]] \
  || fail "plain HTTP unexpectedly reached the HTTPS-only Wazuh intake"

compose_scope wazuh exec -T wazuh-manager python3 - <<'PY'
from pathlib import Path
from urllib import error, request
import json

secret = Path("/run/secrets/wazuh-ingest-shared-secret").read_text().strip()
payload = json.dumps(
    {
        "id": "phase67-proxy-bypass-negative",
        "timestamp": "2026-07-28T00:00:00+00:00",
        "rule": {"id": "5710", "level": 10, "description": "negative"},
        "manager": {"name": "wazuh.manager"},
        "data": {"source_family": "wazuh_detection"},
    }
).encode()
probe = request.Request(
    "http://control-plane:8080/intake/wazuh",
    data=payload,
    headers={
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
        "X-Forwarded-Proto": "https",
    },
    method="POST",
)
try:
    request.urlopen(probe, timeout=5)
except error.HTTPError as exc:
    if exc.code != 403:
        raise SystemExit(f"direct backend bypass returned HTTP {exc.code}, expected 403")
else:
    raise SystemExit("direct backend bypass unexpectedly succeeded")
PY

negative_after_alert_count="$(analyst_queue_count)"
[[ "${negative_after_alert_count}" == "${negative_baseline_alert_count}" ]] \
  || fail "negative boundary tests changed authoritative analyst-queue alert state"

receipt_file="/var/ossec/logs/integrations/aegisops-receipts.jsonl"
receipt_count() {
  compose_scope wazuh exec -T wazuh-manager \
    sh -c '
      if [ -s "$1" ]; then
        wc -l <"$1"
      else
        printf "0\n"
      fi
    ' phase67 "${receipt_file}"
}

initial_receipt_count="$(receipt_count)"
[[ "${initial_receipt_count}" =~ ^[0-9]+$ ]] \
  || fail "could not determine the initial Wazuh receipt count"

compose_scope wazuh exec -T wazuh-manager \
  sh -c '
    touch "$1"
    chown root:wazuh "$1"
    chmod 0640 "$1"
  ' phase67 /var/ossec/logs/aegisops-phase67-ssh-test.log
test_timestamp="$(LC_ALL=C date -u '+%b %e %H:%M:%S')"
compose_scope wazuh exec -T wazuh-manager \
  sh -c '
    printf "%s phase67-test-endpoint sshd[6702]: Failed password for invalid user aegisops-phase67-invalid from 192.0.2.67 port 5067 ssh2\n" "$1" >>"$2"
  ' phase67 "${test_timestamp}" /var/ossec/logs/aegisops-phase67-ssh-test.log

receipt_deadline=$((SECONDS + 90))
first_receipt=""
while ((SECONDS < receipt_deadline)); do
  current_receipt_count="$(receipt_count)"
  if ((current_receipt_count > initial_receipt_count)); then
    first_receipt="$(
      compose_scope wazuh exec -T wazuh-manager \
        sed -n "$((initial_receipt_count + 1))p" "${receipt_file}"
    )"
    break
  fi
  sleep 2
done
[[ -n "${first_receipt}" ]] \
  || fail "no real Wazuh Integrator receipt appeared within 90 seconds"
jq -e '
  .source_mode == "real_wazuh"
  and .http_status == 202
  and .disposition == "created"
' <<<"${first_receipt}" >/dev/null \
  || fail "first real Wazuh delivery did not create one AegisOps alert"
sleep 4
pre_replay_receipt_count="$(receipt_count)"
[[ "${pre_replay_receipt_count//[[:space:]]/}" == "$((initial_receipt_count + 1))" ]] \
  || fail "single trial event produced an unexpected number of Wazuh receipts"

native_alert_id="$(jq -er '.native_wazuh_alert_id' <<<"${first_receipt}")"
replay_file="/tmp/aegisops-phase67-replay-${native_alert_id//[^A-Za-z0-9._-]/_}.json"
compose_scope wazuh exec -T wazuh-manager \
  python3 - "${native_alert_id}" "${replay_file}" <<'PY'
from pathlib import Path
import json
import sys

native_id = sys.argv[1]
destination = Path(sys.argv[2])
alerts_path = Path("/var/ossec/logs/alerts/alerts.json")
for line in reversed(alerts_path.read_text(encoding="utf-8").splitlines()):
    try:
        alert = json.loads(line)
    except json.JSONDecodeError:
        continue
    if str(alert.get("id", "")) == native_id:
        destination.write_text(
            json.dumps(alert, separators=(",", ":"), ensure_ascii=True),
            encoding="utf-8",
        )
        destination.chmod(0o600)
        break
else:
    raise SystemExit(f"native alert {native_id!r} is missing from alerts.json")
PY

compose_scope wazuh exec -T wazuh-manager \
  /var/ossec/integrations/custom-aegisops \
  "${replay_file}" \
  file-bound \
  https://proxy:8443/intake/wazuh >/dev/null
compose_scope wazuh exec -T wazuh-manager rm -f "${replay_file}"

duplicate_receipt=""
duplicate_receipt_index=$((initial_receipt_count + 2))
receipt_deadline=$((SECONDS + 30))
while ((SECONDS < receipt_deadline)); do
  current_receipt_count="$(receipt_count)"
  current_receipt_count="${current_receipt_count//[[:space:]]/}"
  if ((current_receipt_count >= duplicate_receipt_index)); then
    [[ "${current_receipt_count}" == "${duplicate_receipt_index}" ]] \
      || fail "replay produced an unexpected number of Wazuh receipts"
    duplicate_receipt="$(
      compose_scope wazuh exec -T wazuh-manager \
        sed -n "${duplicate_receipt_index}p" "${receipt_file}"
    )"
    break
  fi
  sleep 1
done
[[ -n "${duplicate_receipt}" ]] \
  || fail "duplicate Wazuh receipt did not appear within 30 seconds"
jq -e \
  --arg native_alert_id "${native_alert_id}" \
  --arg alert_id "$(jq -er '.aegisops_alert_id' <<<"${first_receipt}")" '
    .native_wazuh_alert_id == $native_alert_id
    and .http_status == 202
    and .disposition == "deduplicated"
    and .aegisops_alert_id == $alert_id
  ' <<<"${duplicate_receipt}" >/dev/null \
  || fail "duplicate Wazuh delivery did not deduplicate to the original alert"

queue="$(
  compose_scope wazuh exec -T control-plane \
    python3 main.py inspect-analyst-queue
)"
aegisops_alert_id="$(jq -er '.aegisops_alert_id' <<<"${first_receipt}")"
queue_record="$(
  jq -ce --arg alert_id "${aegisops_alert_id}" '
    .records[]
    | select(.alert_id == $alert_id)
  ' <<<"${queue}"
)"
jq -e '
  .source_system == "wazuh"
  and .case_id == null
  and .reviewed_context.source.source_family == "wazuh_detection"
' <<<"${queue_record}" >/dev/null \
  || fail "admitted Wazuh alert is missing from the unpromoted analyst queue"

native_metadata="$(
  compose_scope wazuh exec -T wazuh-manager \
    python3 - "${native_alert_id}" <<'PY'
from pathlib import Path
import json
import sys

native_id = sys.argv[1]
for line in reversed(
    Path("/var/ossec/logs/alerts/alerts.json")
    .read_text(encoding="utf-8")
    .splitlines()
):
    try:
        alert = json.loads(line)
    except json.JSONDecodeError:
        continue
    if str(alert.get("id", "")) == native_id:
        print(
            json.dumps(
                {
                    "manager_id": alert["manager"]["name"],
                    "rule_id": str(alert["rule"]["id"]),
                    "timestamp": alert["timestamp"],
                },
                separators=(",", ":"),
            )
        )
        break
else:
    raise SystemExit(f"native alert {native_id!r} is missing from alerts.json")
PY
)"

[[ "$(git -C "${REPO_ROOT}" rev-parse HEAD)" == "${repository_revision}" ]] \
  || fail "repository revision changed during the Wazuh intake trial"
write_artifact_manifests
capture_artifact_digests
[[ "${worktree_artifact_digest}" == "${initial_artifact_digest}" ]] \
  || fail "Phase 67 artifacts changed during the Wazuh intake trial"
captured_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
evidence_file="$(
  mktemp "${AEGISOPS_LAB_EVIDENCE_DIR}/wazuh-intake-${captured_at//[:]/}.XXXXXX"
)"
jq -n \
  --arg captured_at "${captured_at}" \
  --arg repository_revision "${repository_revision}" \
  --arg worktree_artifact_digest "${worktree_artifact_digest}" \
  --arg runtime_artifact_digest "${runtime_artifact_digest}" \
  --arg native_alert_id "${native_alert_id}" \
  --arg manager_id "$(jq -er '.manager_id' <<<"${native_metadata}")" \
  --arg rule_id "$(jq -er '.rule_id' <<<"${native_metadata}")" \
  --arg timestamp "$(jq -er '.timestamp' <<<"${native_metadata}")" \
  --argjson first_delivery "${first_receipt}" \
  --argjson duplicate_delivery "${duplicate_receipt}" \
  --argjson queue_record "${queue_record}" \
  --argjson negative_baseline_alert_count "${negative_baseline_alert_count}" \
  --argjson negative_after_alert_count "${negative_after_alert_count}" '
    {
      schema_version: "phase67-wazuh-intake-evidence-v1",
      source_mode: "real_wazuh",
      fixture_provenance: "live_capture_sanitized",
      captured_at: $captured_at,
      repository_revision: $repository_revision,
      worktree_artifact_digest: $worktree_artifact_digest,
      runtime_artifact_digest: $runtime_artifact_digest,
      wazuh_manager_health: "healthy",
      native_wazuh_alert_id: $native_alert_id,
      native_wazuh_manager_id: $manager_id,
      native_wazuh_rule_id: $rule_id,
      native_event_timestamp: $timestamp,
      negative_boundary: {
        baseline_alert_count: $negative_baseline_alert_count,
        after_alert_count: $negative_after_alert_count,
        authoritative_alert_delta: (
          $negative_after_alert_count - $negative_baseline_alert_count
        )
      },
      first_delivery: (
        $first_delivery
        | {
            http_status,
            disposition,
            aegisops_alert_id,
            finding_id,
            reconciliation_id
          }
      ),
      duplicate_delivery: (
        $duplicate_delivery
        | {
            http_status,
            disposition,
            aegisops_alert_id,
            finding_id,
            reconciliation_id
          }
      ),
      analyst_queue: {
        source_system: $queue_record.source_system,
        alert_id: $queue_record.alert_id,
        case_id: $queue_record.case_id
      },
      case_promotion: "not_performed",
      authority_boundary: "aegisops_admission_is_authoritative"
    }
  ' >"${evidence_file}"
chmod 600 "${evidence_file}"

echo "PASS missing_bearer_secret=403"
echo "PASS invalid_bearer_secret=403"
echo "PASS malformed_payload=400"
echo "PASS unsupported_source_family=400"
echo "PASS oversized_payload=413"
echo "PASS proxy_bypass=403"
echo "PASS negative_authoritative_alert_delta=0"
echo "PASS native_wazuh_alert_id=${native_alert_id}"
echo "PASS first_disposition=created"
echo "PASS duplicate_disposition=deduplicated"
echo "PASS analyst_queue_alert_id=${aegisops_alert_id}"
echo "evidence=${evidence_file}"
