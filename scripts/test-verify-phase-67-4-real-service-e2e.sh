#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
schema="${repo_root}/control-plane/deployment/phase-67-integration-lab/e2e/evidence-manifest.schema.json"
sample="${repo_root}/control-plane/deployment/phase-67-integration-lab/e2e/sample-evidence.json"
validator="${repo_root}/control-plane/deployment/phase-67-integration-lab/e2e/validate_evidence_manifest.py"
source_verifier="${repo_root}/scripts/verify-phase-67-4-real-service-e2e.sh"
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
  # compatibility fingerprint and returns it to the current schema contract.
  if jq -e --arg trial "phase67-e2e-20260801T135206Z-26c533b6ca31" \
    --arg revision "2473b66f5702a38f1d4630c990509bf812a6af7a" \
    '.verdict as $verdict
    | .trial_run_id == $trial
      and .snapshot.repository_revision == $revision
      and ([
        "integration_trial_passed_with_owned_limitations",
        "integration_trial_blocked",
        "integration_trial_failed"
      ] | index($verdict) != null)' \
    "${manifest}" >/dev/null; then
    expected='does not match the validator schema'
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

assert_schema_fails_with() {
  local name="$1"
  local expected="$2"
  local expression="$3"
  local mutated_schema="${workdir}/${name}-schema.json"
  jq "${expression}" "${schema}" >"${mutated_schema}"
  if python3 "${validator}" "${mutated_schema}" "${sample}" \
    >"${workdir}/${name}.out" 2>"${workdir}/${name}.err"; then
    echo "self-test expected schema rejection for ${name}" >&2
    exit 1
  fi
  grep -Fq -- "${expected}" "${workdir}/${name}.err" \
    || {
      cat "${workdir}/${name}.err" >&2
      echo "self-test ${name} missed schema diagnostic: ${expected}" >&2
      exit 1
    }
}

source_fixture="${workdir}/source-verifier-fixture"
source_fixture_lab="${source_fixture}/control-plane/deployment/phase-67-integration-lab"
source_fixture_runner="${source_fixture_lab}/run-e2e-trial.sh"

prepare_source_fixture() {
  mkdir -p \
    "${source_fixture}/control-plane/deployment" \
    "${source_fixture_lab}"
  ln -s "${repo_root}/README.md" "${source_fixture}/README.md"
  ln -s "${repo_root}/docs" "${source_fixture}/docs"
  ln -s \
    "${repo_root}/control-plane/aegisops" \
    "${source_fixture}/control-plane/aegisops"
  ln -s \
    "${repo_root}/control-plane/tests" \
    "${source_fixture}/control-plane/tests"
  for entry in e2e shuffle README.md RUNBOOK.md test-wazuh-intake.sh; do
    ln -s \
      "${repo_root}/control-plane/deployment/phase-67-integration-lab/${entry}" \
      "${source_fixture_lab}/${entry}"
  done
}

reset_source_fixture_runner() {
  cp \
    "${repo_root}/control-plane/deployment/phase-67-integration-lab/run-e2e-trial.sh" \
    "${source_fixture_runner}"
  chmod +x "${source_fixture_runner}"
}

replace_source_once() {
  local old="$1"
  local new="$2"
  local path="$3"
  python3 - "${old}" "${new}" "${path}" <<'PY'
from pathlib import Path
import sys

old, new, raw_path = sys.argv[1:]
path = Path(raw_path)
source = path.read_text(encoding="utf-8")
if source.count(old) != 1:
    raise SystemExit(f"expected exactly one source match, found {source.count(old)}")
path.write_text(source.replace(old, new, 1), encoding="utf-8")
PY
}

replace_source_all() {
  local old="$1"
  local new="$2"
  local path="$3"
  python3 - "${old}" "${new}" "${path}" <<'PY'
from pathlib import Path
import sys

old, new, raw_path = sys.argv[1:]
path = Path(raw_path)
source = path.read_text(encoding="utf-8")
if old not in source:
    raise SystemExit("source mutation target is missing")
path.write_text(source.replace(old, new), encoding="utf-8")
PY
}

assert_source_verifier_fails() {
  local name="$1"
  local expected="$2"
  shift 2
  reset_source_fixture_runner
  "$@" "${source_fixture_runner}"
  if AEGISOPS_REPO_ROOT_OVERRIDE="${source_fixture}" \
    bash "${source_verifier}" \
    >"${workdir}/${name}.out" 2>"${workdir}/${name}.err"; then
    echo "self-test expected source verifier rejection for ${name}" >&2
    exit 1
  fi
  grep -Fq -- "${expected}" "${workdir}/${name}.err" \
    || {
      cat "${workdir}/${name}.err" >&2
      echo "self-test ${name} missed expected diagnostic: ${expected}" >&2
      exit 1
    }
}

python3 "${validator}" "${schema}" "${sample}"
assert_schema_fails_with \
  reordered-current-journey \
  'schema current step journey contract drifted' \
  '.["$defs"].current_step_journey.properties.steps.prefixItems[0].properties.name.const = "wrong-step"'
assert_schema_fails_with \
  nullable-passed-requester \
  'schema profile, journey, and passed-verdict selection drifted' \
  '(.allOf[] | select(.if.properties.verdict.const == "integration_trial_passed_with_owned_limitations") | .then.properties.human_control.properties.requester_identity.type) = ["string", "null"]'
assert_schema_fails_with \
  missing-passed-restart-proof \
  'schema profile, journey, and passed-verdict selection drifted' \
  'del(.allOf[] | select(.if.properties.verdict.const == "integration_trial_passed_with_owned_limitations") | .then.properties.restart)'
assert_schema_fails_with \
  missing-passed-replay-observation \
  'schema profile, journey, and passed-verdict selection drifted' \
  '(.allOf[] | select(.if.properties.verdict.const == "integration_trial_passed_with_owned_limitations") | .then.properties.idempotency.required) -= ["wazuh_replay_observed_at"]'
assert_schema_fails_with \
  missing-passed-negative-observation \
  'schema profile, journey, and passed-verdict selection drifted' \
  'del(.allOf[] | select(.if.properties.verdict.const == "integration_trial_passed_with_owned_limitations") | .then.properties.negative_cases.properties.invalid_credential.required)'
assert_schema_fails_with \
  passed-ga-accepted \
  'schema profile, journey, and passed-verdict selection drifted' \
  '(.allOf[] | select(.if.properties.verdict.const == "integration_trial_passed_with_owned_limitations") | .then.properties.evaluation.properties.ga_accepted.const) = true'

prepare_source_fixture

assert_source_verifier_fails \
  reintroduced-manual-action-service \
  'contains forbidden text: docker_lab service create' \
  replace_source_once \
  'shuffle_action_service="shuffle-tools_1-2-0"' \
  $'shuffle_action_service="shuffle-tools_1-2-0"\n# forbidden historical lifecycle: docker_lab service create'

assert_source_verifier_fails \
  reintroduced-fixed-action-port \
  'contains forbidden text: shuffle_action_service_port=33334' \
  replace_source_all \
  'shuffle_action_service_port=""' \
  'shuffle_action_service_port=33334'

assert_source_verifier_fails \
  removed-action-runtime-id-guard \
  'missing required text: shuffle_action_runtime_matches_reviewed_image' \
  replace_source_all \
  'shuffle_action_runtime_matches_reviewed_image' \
  'shuffle_action_runtime_check_removed'

assert_source_verifier_fails \
  removed-action-stability-guard \
  'missing required text: shuffle_action_service_observation_is_stable' \
  replace_source_all \
  'shuffle_action_service_observation_is_stable' \
  'shuffle_action_service_stability_check_removed'

assert_source_verifier_fails \
  removed-stop-before-remove-guard \
  'exit cleanup must stop Orborus before exact-ID removal' \
  replace_source_once \
  $'    "${LAB_DIR}/cleanup.sh" >/dev/null 2>&1 || cleanup_failed=true\n    remove_reviewed_shuffle_action_service >/dev/null 2>&1 \\\n      || cleanup_failed=true' \
  $'    remove_reviewed_shuffle_action_service >/dev/null 2>&1 \\\n      || cleanup_failed=true\n    "${LAB_DIR}/cleanup.sh" >/dev/null 2>&1 || cleanup_failed=true'

assert_source_verifier_fails \
  removed-restart-worker-cleanup \
  'restart must stop, remove exact IDs, start, and re-claim in order' \
  replace_source_once \
  $'run_reviewed_lab_command remove_reviewed_shuffle_action_service\nrun_reviewed_lab_command remove_reviewed_shuffle_worker_service\nrun_reviewed_lab_command assert_shuffle_action_service_absent' \
  $'run_reviewed_lab_command remove_reviewed_shuffle_action_service\n# worker cleanup guard removed\nrun_reviewed_lab_command assert_shuffle_action_service_absent'

assert_source_verifier_fails \
  published-manifest-before-validation \
  'manifest must be validated before its atomic publication' \
  replace_source_once \
  'mv "${evidence_output}" "${publication_manifest_candidate}"' \
  $'mv "${evidence_output}" "${publication_manifest_candidate}"\nln "${publication_manifest_candidate}" "${final_evidence}" # forbidden early commit'

assert_source_verifier_fails \
  duplicate-callback-accepted \
  'missing required text: select(startswith("CALLBACK_URL="))' \
  replace_source_all \
  'select(startswith("CALLBACK_URL="))' \
  'select(. == ("CALLBACK_URL=" + $callback_url))'

assert_source_verifier_fails \
  wrong-callback-accepted \
  'missing required text: $callbacks[0] == ("CALLBACK_URL=" + $callback_url)' \
  replace_source_all \
  '$callbacks[0] == ("CALLBACK_URL=" + $callback_url)' \
  '($callbacks[0] | startswith("CALLBACK_URL="))'

runtime_images="${workdir}/runtime-images.json"
jq '
  .snapshot.images
  + [
      {
        service: "wazuh-security-bootstrap",
        immutable_reference: "wazuh/wazuh-indexer:4.14.6@sha256:27261711c6479e2e503171918aae9a23b3fc4dcfc2d28d204e75985c1e0fb4c5"
      },
      {
        service: "shuffle-worker-image",
        immutable_reference: "ghcr.io/shuffle/shuffle-worker:2.2.1@sha256:9541c1fef2bc8511727610b565adbd0f7c817c53afee2dd9fef6aad8a971ffb1"
      }
  ]
  | map(
      if .service == "shuffle-action-image"
        or .service == "shuffle-worker-image"
      then . + {runtime_image_id: ("sha256:" + ("f" * 64))}
      else .
      end
    )
  | sort_by(.service)
' "${sample}" >"${runtime_images}"
python3 "${validator}" --runtime-images "${runtime_images}"

missing_action_runtime_image="${workdir}/missing-action-runtime-image.json"
jq '
  map(
    if .service == "shuffle-action-image"
    then del(.runtime_image_id)
    else .
    end
  )
' "${runtime_images}" >"${missing_action_runtime_image}"
if python3 "${validator}" --runtime-images "${missing_action_runtime_image}" \
  >"${workdir}/missing-action-runtime-image.out" \
  2>"${workdir}/missing-action-runtime-image.err"; then
  echo "self-test expected missing action runtime image rejection" >&2
  exit 1
fi
grep -Fq -- \
  'must retain observed Shuffle action and worker runtime image IDs' \
  "${workdir}/missing-action-runtime-image.err"

missing_worker_runtime_image="${workdir}/missing-worker-runtime-image.json"
jq '
  map(
    if .service == "shuffle-worker-image"
    then del(.runtime_image_id)
    else .
    end
  )
' "${runtime_images}" >"${missing_worker_runtime_image}"
if python3 "${validator}" --runtime-images "${missing_worker_runtime_image}" \
  >"${workdir}/missing-worker-runtime-image.out" \
  2>"${workdir}/missing-worker-runtime-image.err"; then
  echo "self-test expected missing worker runtime image rejection" >&2
  exit 1
fi
grep -Fq -- \
  'must retain observed Shuffle action and worker runtime image IDs' \
  "${workdir}/missing-worker-runtime-image.err"

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
