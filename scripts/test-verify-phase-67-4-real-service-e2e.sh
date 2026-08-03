#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
schema="${repo_root}/control-plane/deployment/phase-67-integration-lab/e2e/evidence-manifest.schema.json"
sample="${repo_root}/control-plane/deployment/phase-67-integration-lab/e2e/sample-evidence.json"
validator="${repo_root}/control-plane/deployment/phase-67-integration-lab/e2e/validate_evidence_manifest.py"
workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

assert_fails_with() {
  local name="$1"
  local expected="$2"
  local manifest="${workdir}/${name}.json"
  shift 2
  cp "${sample}" "${manifest}"
  "$@" "${manifest}"
  # Any mutation of the retained historical packet invalidates its immutable
  # compatibility fingerprint and returns it to the current image contract.
  if jq -e --arg trial "phase67-e2e-20260801T135206Z-26c533b6ca31" \
    --arg revision "2473b66f5702a38f1d4630c990509bf812a6af7a" \
    '.verdict as $verdict
    | .trial_run_id == $trial
      and .snapshot.repository_revision == $revision
      and ([
        "integration_trial_passed_ga_not_accepted",
        "integration_trial_passed_with_owned_limitations",
        "integration_trial_blocked",
        "integration_trial_failed"
      ] | index($verdict) != null)' \
    "${manifest}" >/dev/null; then
    expected='complete reviewed full-profile service inventory'
  fi
  if python3 "${validator}" "${schema}" "${manifest}" \
    >"${workdir}/${name}.out" 2>"${workdir}/${name}.err"; then
    echo "self-test expected rejection for ${name}" >&2
    exit 1
  fi
  grep -Fq -- "${expected}" "${workdir}/${name}.err" \
    || {
      cat "${workdir}/${name}.err" >&2
      echo "self-test ${name} missed expected diagnostic: ${expected}" >&2
      exit 1
    }
}

mutate_json() {
  local expression="$1"
  local path="$2"
  local staging="${path}.tmp"
  jq "${expression}" "${path}" >"${staging}"
  mv "${staging}" "${path}"
}

python3 "${validator}" "${schema}" "${sample}"
runtime_images="${workdir}/runtime-images.json"
jq '
  .snapshot.images
  + [{
      service: "wazuh-security-bootstrap",
      immutable_reference: "wazuh/wazuh-indexer:4.14.6@sha256:27261711c6479e2e503171918aae9a23b3fc4dcfc2d28d204e75985c1e0fb4c5"
    }]
  | sort_by(.service)
' "${sample}" >"${runtime_images}"
python3 "${validator}" --runtime-images "${runtime_images}"

assert_fails_with \
  placeholder-id \
  'looks synthetic or placeholder-derived' \
  mutate_json '.identifiers.native_wazuh_alert_id = "fixture-alert-1"'
assert_fails_with \
  unobserved-shuffle-id \
  'must be null' \
  mutate_json '.identifiers.shuffle_execution_id = "shuffle-run-123"'
assert_fails_with \
  missing-step \
  'exactly 15 steps' \
  mutate_json 'del(.steps[14])'
assert_fails_with \
  mixed-snapshot \
  'mixed snapshot' \
  mutate_json '.steps[8].snapshot_id = "phase67-snapshot-fedcba9876543210"'
assert_fails_with \
  unbound-blocked-snapshot \
  'not bound to all snapshot inputs' \
  mutate_json '.snapshot.docker_context = "tampered-colima"'
assert_fails_with \
  incomplete-runtime-image-inventory \
  'complete reviewed full-profile service inventory' \
  mutate_json '.snapshot.images |= map(select(.service == "shuffle-action-image"))'
assert_fails_with \
  unreviewed-shuffle-action-image \
  'does not use the reviewed immutable reference' \
  mutate_json '(.snapshot.images[] | select(.service == "shuffle-action-image") | .immutable_reference) = "frikky/shuffle@sha256:9999999999999999999999999999999999999999999999999999999999999999"'
assert_fails_with \
  non-chronological-blocked-steps \
  'strictly chronological' \
  mutate_json '.steps[1].observed_at = .steps[0].observed_at'
assert_fails_with \
  unreviewed-step-reference \
  'historical trial contract' \
  mutate_json '.steps[5].evidence_refs = ["fake"]'
assert_fails_with \
  missing-historical-approval-blocker \
  'historical approval-blocked limitation contract is incomplete' \
  mutate_json '.limitations[0].limitation_id = "unrelated-blocker"'
assert_fails_with \
  downgraded-historical-approval-blocker \
  'historical approval-blocked limitation contract is incomplete' \
  mutate_json '.limitations[0].status = "accepted"'
assert_fails_with \
  impossible-failed-order \
  'exactly one failed step' \
  mutate_json '.verdict = "integration_trial_failed"
    | .steps[7].status = "failed"
    | .steps[9].status = "failed"
    | .steps[9].blocker = {
        "owner": "AegisOps integration engineering",
        "reason": "A later step cannot run after an upstream failure."
      }'
assert_fails_with \
  unobserved-receipt-probe \
  'must be null when run_negative_cases did not pass' \
  mutate_json '.negative_cases.failed_execution = {
    "status": "contained",
    "authority_before": 1,
    "authority_after": 1,
    "authority_delta": 0,
    "measurement_source": "aegisops_authoritative_record_count",
    "evidence_ref": "journey:negative-probe"
  }'
assert_fails_with \
  same-actor \
  'a non-passed approval step cannot claim an approver or approval event' \
  mutate_json '.human_control.approver_identity = .human_control.requester_identity'
assert_fails_with \
  denied-dispatch \
  'denied action must produce no dispatch' \
  mutate_json '.human_control.denied_action_execution_count = 1'
assert_fails_with \
  inferred-reconciliation \
  'a non-passed receipt replay step cannot claim Shuffle replay success' \
  mutate_json '.idempotency.receipt_replay_reconciliation_id = "reconciliation-second"'
assert_fails_with \
  secret-exposure \
  'contains a secret value or private host path' \
  mutate_json '.limitations[0].description = "Bearer leaked-value"'
assert_fails_with \
  private-host-path \
  'contains a secret value or private host path' \
  mutate_json '.limitations[0].description = "/Users/operator/private/evidence.json"' # publishable-path-hygiene: allowlist -- adversarial fixture
assert_fails_with \
  inferred-report \
  'a non-passed report step cannot claim a report export' \
  mutate_json '.report.source_of_truth = "shuffle_execution_state"'
assert_fails_with \
  ga-overclaim \
  'not in the reviewed vocabulary' \
  mutate_json '.verdict = "ga_accepted"'

echo "PASS: Phase 67.4 verifier adversarial self-tests passed."
