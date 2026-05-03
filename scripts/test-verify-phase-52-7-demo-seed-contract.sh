#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-7-demo-seed-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/fixtures/demo-seed"
  printf '%s\n' "# AegisOps" "See [Phase 52.7 demo seed contract](docs/deployment/demo-seed-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/demo-seed-contract.md" \
    "${target}/docs/deployment/demo-seed-contract.md"
  cp "${repo_root}/docs/deployment/fixtures/demo-seed/"*.json \
    "${target}/docs/deployment/fixtures/demo-seed/"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

remove_text_from_contract() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/deployment/demo-seed-contract.md"
}

set_fixture_json_value() {
  local target="$1"
  local fixture="$2"
  local expression="$3"

  python3 - "${target}/docs/deployment/fixtures/demo-seed/${fixture}" "${expression}" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
expression = sys.argv[2]
payload = json.loads(path.read_text(encoding="utf-8"))
exec(expression, {"payload": payload})
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/demo-seed-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 52.7 demo seed contract"

missing_record_row_repo="${workdir}/missing-record-row"
create_valid_repo "${missing_record_row_repo}"
remove_text_from_contract "${missing_record_row_repo}" \
  "| Demo approval | Explicit demo approval identifier, demo labels, linked demo action request, and reviewer placeholder. | Must render as demo-only approval rehearsal. | Must not satisfy real approval truth, release gate truth, execution authorization, or customer evidence. |"
assert_fails_with \
  "${missing_record_row_repo}" \
  "Missing complete Phase 52.7 seed record row: Demo approval"

missing_label_row_repo="${workdir}/missing-label-row"
create_valid_repo "${missing_label_row_repo}"
remove_text_from_contract "${missing_label_row_repo}" \
  '| `not-production-truth` | Required on every demo seed record. | Missing label fails because demo data must never be presented as production truth. |'
assert_fails_with \
  "${missing_label_row_repo}" \
  "Missing complete Phase 52.7 demo label row: not-production-truth"

missing_reset_row_repo="${workdir}/missing-reset-row"
create_valid_repo "${missing_reset_row_repo}"
remove_text_from_contract "${missing_reset_row_repo}" \
  '| Production guard | Reset must prove `deletes_production_records=false` and must not touch records outside the demo bundle. | Any reset plan that can delete production, imported, customer-private, or unlabeled records fails. |'
assert_fails_with \
  "${missing_reset_row_repo}" \
  "Missing complete Phase 52.7 reset boundary row: Production guard"

missing_fixture_repo="${workdir}/missing-fixture"
create_valid_repo "${missing_fixture_repo}"
rm "${missing_fixture_repo}/docs/deployment/fixtures/demo-seed/missing-label.json"
assert_fails_with \
  "${missing_fixture_repo}" \
  "Missing Phase 52.7 demo seed fixture: missing-label.json"

valid_missing_label_repo="${workdir}/valid-missing-label"
create_valid_repo "${valid_missing_label_repo}"
set_fixture_json_value \
  "${valid_missing_label_repo}" \
  "valid-demo-seed.json" \
  "payload['records'][0]['labels'].remove('not-production-truth')"
assert_fails_with \
  "${valid_missing_label_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_missing_demo_alert_field_repo="${workdir}/valid-missing-demo-alert-field"
create_valid_repo "${valid_missing_demo_alert_field_repo}"
set_fixture_json_value \
  "${valid_missing_demo_alert_field_repo}" \
  "valid-demo-seed.json" \
  "del payload['records'][0]['fixture_provenance']"
assert_fails_with \
  "${valid_missing_demo_alert_field_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_missing_required_family_repo="${workdir}/valid-missing-required-family"
create_valid_repo "${valid_missing_required_family_repo}"
set_fixture_json_value \
  "${valid_missing_required_family_repo}" \
  "valid-demo-seed.json" \
  "payload['records'] = [record for record in payload['records'] if record.get('type') != 'demo-recommendation']"
assert_fails_with \
  "${valid_missing_required_family_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_missing_family_linkage_repo="${workdir}/valid-missing-family-linkage"
create_valid_repo "${valid_missing_family_linkage_repo}"
set_fixture_json_value \
  "${valid_missing_family_linkage_repo}" \
  "valid-demo-seed.json" \
  "payload['records'][2]['linked_demo_signal_id'] = 'missing-demo-signal'"
assert_fails_with \
  "${valid_missing_family_linkage_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_missing_action_request_linkage_repo="${workdir}/valid-missing-action-request-linkage"
create_valid_repo "${valid_missing_action_request_linkage_repo}"
set_fixture_json_value \
  "${valid_missing_action_request_linkage_repo}" \
  "valid-demo-seed.json" \
  "payload['records'].append({'type': 'demo-action-request', 'id': 'demo-action-request-001', 'linked_demo_case_id': 'missing-demo-case', 'requested_action': 'isolate demo host', 'non_production_scope': True, 'presentation': 'demo-only action rehearsal', 'labels': ['demo-only', 'first-user-rehearsal', 'not-production-truth'], 'production_claim': False, 'truth_surfaces': [], 'authority': 'demo_rehearsal_only'})"
assert_fails_with \
  "${valid_missing_action_request_linkage_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_missing_approval_linkage_repo="${workdir}/valid-missing-approval-linkage"
create_valid_repo "${valid_missing_approval_linkage_repo}"
set_fixture_json_value \
  "${valid_missing_approval_linkage_repo}" \
  "valid-demo-seed.json" \
  "payload['records'].append({'type': 'demo-action-request', 'id': 'demo-action-request-001', 'linked_demo_case_id': 'demo-case-001', 'requested_action': 'isolate demo host', 'non_production_scope': True, 'presentation': 'demo-only action rehearsal', 'labels': ['demo-only', 'first-user-rehearsal', 'not-production-truth'], 'production_claim': False, 'truth_surfaces': [], 'authority': 'demo_rehearsal_only'}); payload['records'].append({'type': 'demo-approval', 'id': 'demo-approval-001', 'linked_demo_action_request_id': 'missing-demo-action-request', 'reviewer_placeholder': 'Demo reviewer', 'presentation': 'demo-only approval rehearsal', 'labels': ['demo-only', 'first-user-rehearsal', 'not-production-truth'], 'production_claim': False, 'truth_surfaces': [], 'authority': 'demo_rehearsal_only'})"
assert_fails_with \
  "${valid_missing_approval_linkage_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_missing_reconciliation_note_linkage_repo="${workdir}/valid-missing-reconciliation-note-linkage"
create_valid_repo "${valid_missing_reconciliation_note_linkage_repo}"
set_fixture_json_value \
  "${valid_missing_reconciliation_note_linkage_repo}" \
  "valid-demo-seed.json" \
  "payload['records'].append({'type': 'demo-reconciliation-note', 'id': 'demo-reconciliation-note-001', 'linked_demo_execution_receipt_id': 'missing-demo-execution-receipt', 'outcome_placeholder': 'Demo outcome note', 'presentation': 'demo-only reconciliation rehearsal', 'labels': ['demo-only', 'first-user-rehearsal', 'not-production-truth'], 'production_claim': False, 'truth_surfaces': [], 'authority': 'demo_rehearsal_only'})"
assert_fails_with \
  "${valid_missing_reconciliation_note_linkage_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_duplicate_required_family_repo="${workdir}/valid-duplicate-required-family"
create_valid_repo "${valid_duplicate_required_family_repo}"
set_fixture_json_value \
  "${valid_duplicate_required_family_repo}" \
  "valid-demo-seed.json" \
  "payload['records'].append(dict(payload['records'][3], id='demo-case-duplicate'))"
assert_fails_with \
  "${valid_duplicate_required_family_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_non_repeatable_seed_repo="${workdir}/valid-non-repeatable-seed"
create_valid_repo "${valid_non_repeatable_seed_repo}"
set_fixture_json_value \
  "${valid_non_repeatable_seed_repo}" \
  "valid-demo-seed.json" \
  "payload['repeatability']['load_strategy'] = 'append-new-demo-records'"
assert_fails_with \
  "${valid_non_repeatable_seed_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

negative_label_false_pass_repo="${workdir}/negative-label-false-pass"
create_valid_repo "${negative_label_false_pass_repo}"
cp \
  "${negative_label_false_pass_repo}/docs/deployment/fixtures/demo-seed/valid-demo-seed.json" \
  "${negative_label_false_pass_repo}/docs/deployment/fixtures/demo-seed/missing-label.json"
assert_fails_with \
  "${negative_label_false_pass_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for missing-label.json: expected rejection"

destructive_reset_false_pass_repo="${workdir}/destructive-reset-false-pass"
create_valid_repo "${destructive_reset_false_pass_repo}"
cp \
  "${destructive_reset_false_pass_repo}/docs/deployment/fixtures/demo-seed/valid-demo-seed.json" \
  "${destructive_reset_false_pass_repo}/docs/deployment/fixtures/demo-seed/destructive-reset.json"
assert_fails_with \
  "${destructive_reset_false_pass_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for destructive-reset.json: expected rejection"

valid_broad_reset_selector_repo="${workdir}/valid-broad-reset-selector"
create_valid_repo "${valid_broad_reset_selector_repo}"
set_fixture_json_value \
  "${valid_broad_reset_selector_repo}" \
  "valid-demo-seed.json" \
  "payload['reset']['selector'] = {'bundle': 'phase-52-7-demo-seed', 'labels': ['demo-only', 'first-user-rehearsal']}"
assert_fails_with \
  "${valid_broad_reset_selector_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

valid_string_reset_selector_repo="${workdir}/valid-string-reset-selector"
create_valid_repo "${valid_string_reset_selector_repo}"
set_fixture_json_value \
  "${valid_string_reset_selector_repo}" \
  "valid-demo-seed.json" \
  "payload['reset']['selector'] = 'bundle=phase-52-7-demo-seed AND label=demo-only AND label=first-user-rehearsal AND label=not-production-truth'"
assert_fails_with \
  "${valid_string_reset_selector_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

production_claim_false_pass_repo="${workdir}/production-claim-false-pass"
create_valid_repo "${production_claim_false_pass_repo}"
cp \
  "${production_claim_false_pass_repo}/docs/deployment/fixtures/demo-seed/valid-demo-seed.json" \
  "${production_claim_false_pass_repo}/docs/deployment/fixtures/demo-seed/production-claim.json"
assert_fails_with \
  "${production_claim_false_pass_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for production-claim.json: expected rejection"

valid_custom_truth_surface_repo="${workdir}/valid-custom-truth-surface"
create_valid_repo "${valid_custom_truth_surface_repo}"
set_fixture_json_value \
  "${valid_custom_truth_surface_repo}" \
  "valid-demo-seed.json" \
  "payload['records'][0]['truth_surfaces'] = ['demo_only_projection']"
assert_fails_with \
  "${valid_custom_truth_surface_repo}" \
  "Invalid Phase 52.7 demo seed fixture state for valid-demo-seed.json: expected valid"

demo_truth_repo="${workdir}/demo-production-truth"
create_valid_repo "${demo_truth_repo}"
printf '%s\n' "Demo data is production truth." \
  >>"${demo_truth_repo}/docs/deployment/demo-seed-contract.md"
assert_fails_with \
  "${demo_truth_repo}" \
  "Forbidden Phase 52.7 demo seed contract claim: Demo data is production truth"

destructive_reset_claim_repo="${workdir}/destructive-reset-claim"
create_valid_repo "${destructive_reset_claim_repo}"
printf '%s\n' "Demo reset may delete production records." \
  >>"${destructive_reset_claim_repo}/docs/deployment/demo-seed-contract.md"
assert_fails_with \
  "${destructive_reset_claim_repo}" \
  "Forbidden Phase 52.7 demo seed contract claim: Demo reset may delete production records"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/demo-seed-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.7 demo seed contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 52.7 demo seed contract."

echo "Phase 52.7 demo seed contract negative and valid fixtures passed."
