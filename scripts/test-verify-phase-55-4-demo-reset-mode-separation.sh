#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-55-4-demo-reset-mode-separation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/fixtures/demo-reset-mode-separation"
  printf '%s\n' \
    "# AegisOps" \
    "See [Phase 55.4 demo reset and mode separation contract](docs/deployment/demo-reset-mode-separation.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/deployment/demo-reset-mode-separation.md" \
    "${target}/docs/deployment/demo-reset-mode-separation.md"
  cp "${repo_root}/docs/deployment/fixtures/demo-reset-mode-separation/"*.json \
    "${target}/docs/deployment/fixtures/demo-reset-mode-separation/"
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
    "${target}/docs/deployment/demo-reset-mode-separation.md"
}

set_fixture_json_value() {
  local target="$1"
  local fixture="$2"
  local expression="$3"

  python3 - "${target}/docs/deployment/fixtures/demo-reset-mode-separation/${fixture}" "${expression}" <<'PY'
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
rm "${missing_contract_repo}/docs/deployment/demo-reset-mode-separation.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 55.4 demo reset and mode separation contract"

missing_reset_row_repo="${workdir}/missing-reset-row"
create_valid_repo "${missing_reset_row_repo}"
remove_text_from_contract "${missing_reset_row_repo}" \
  "| Live preservation | Reset must preserve live, production, audit, imported, customer-private, unlabeled, and non-demo workflow records byte-for-byte. | Any deleted live record, changed production-truth field, audit mutation, or customer-data cleanup fails. |"
assert_fails_with \
  "${missing_reset_row_repo}" \
  "Missing complete Phase 55.4 reset boundary row: Live preservation"

missing_mode_row_repo="${workdir}/missing-mode-row"
create_valid_repo "${missing_mode_row_repo}"
remove_text_from_contract "${missing_mode_row_repo}" \
  "| Live | Authoritative workflow mode for AegisOps control-plane records, production truth, audit truth, and customer-bound records. | Demo reset cannot delete, mutate, relabel, close, reconcile, approve, or clean live records. |"
assert_fails_with \
  "${missing_mode_row_repo}" \
  "Missing complete Phase 55.4 mode separation row: Live"

missing_fixture_repo="${workdir}/missing-fixture"
create_valid_repo "${missing_fixture_repo}"
rm "${missing_fixture_repo}/docs/deployment/fixtures/demo-reset-mode-separation/delete-live-record.json"
assert_fails_with \
  "${missing_fixture_repo}" \
  "Missing Phase 55.4 demo reset fixture: delete-live-record.json"

valid_deletes_live_repo="${workdir}/valid-deletes-live"
create_valid_repo "${valid_deletes_live_repo}"
set_fixture_json_value \
  "${valid_deletes_live_repo}" \
  "valid-repeatable-demo-reset.json" \
  "payload['after_records'] = [record for record in payload['after_records'] if record['id'] != 'live-case-001']"
assert_fails_with \
  "${valid_deletes_live_repo}" \
  "Invalid Phase 55.4 demo reset fixture state for valid-repeatable-demo-reset.json: expected valid"

valid_mutates_live_repo="${workdir}/valid-mutates-live"
create_valid_repo "${valid_mutates_live_repo}"
set_fixture_json_value \
  "${valid_mutates_live_repo}" \
  "valid-repeatable-demo-reset.json" \
  "payload['after_records'][2]['status'] = 'closed-by-demo-reset'"
assert_fails_with \
  "${valid_mutates_live_repo}" \
  "Invalid Phase 55.4 demo reset fixture state for valid-repeatable-demo-reset.json: expected valid"

valid_non_repeatable_repo="${workdir}/valid-non-repeatable"
create_valid_repo "${valid_non_repeatable_repo}"
set_fixture_json_value \
  "${valid_non_repeatable_repo}" \
  "valid-repeatable-demo-reset.json" \
  "payload['after_records'].append(dict(payload['after_records'][0], id='demo-case-duplicate'))"
assert_fails_with \
  "${valid_non_repeatable_repo}" \
  "Invalid Phase 55.4 demo reset fixture state for valid-repeatable-demo-reset.json: expected valid"

delete_live_false_pass_repo="${workdir}/delete-live-false-pass"
create_valid_repo "${delete_live_false_pass_repo}"
cp \
  "${delete_live_false_pass_repo}/docs/deployment/fixtures/demo-reset-mode-separation/valid-repeatable-demo-reset.json" \
  "${delete_live_false_pass_repo}/docs/deployment/fixtures/demo-reset-mode-separation/delete-live-record.json"
assert_fails_with \
  "${delete_live_false_pass_repo}" \
  "Invalid Phase 55.4 demo reset fixture state for delete-live-record.json: expected rejection"

mutate_production_false_pass_repo="${workdir}/mutate-production-false-pass"
create_valid_repo "${mutate_production_false_pass_repo}"
cp \
  "${mutate_production_false_pass_repo}/docs/deployment/fixtures/demo-reset-mode-separation/valid-repeatable-demo-reset.json" \
  "${mutate_production_false_pass_repo}/docs/deployment/fixtures/demo-reset-mode-separation/mutate-production-truth.json"
assert_fails_with \
  "${mutate_production_false_pass_repo}" \
  "Invalid Phase 55.4 demo reset fixture state for mutate-production-truth.json: expected rejection"

unlabeled_false_pass_repo="${workdir}/unlabeled-false-pass"
create_valid_repo "${unlabeled_false_pass_repo}"
cp \
  "${unlabeled_false_pass_repo}/docs/deployment/fixtures/demo-reset-mode-separation/valid-repeatable-demo-reset.json" \
  "${unlabeled_false_pass_repo}/docs/deployment/fixtures/demo-reset-mode-separation/unlabeled-record-reset.json"
assert_fails_with \
  "${unlabeled_false_pass_repo}" \
  "Invalid Phase 55.4 demo reset fixture state for unlabeled-record-reset.json: expected rejection"

backup_restore_false_pass_repo="${workdir}/backup-restore-false-pass"
create_valid_repo "${backup_restore_false_pass_repo}"
cp \
  "${backup_restore_false_pass_repo}/docs/deployment/fixtures/demo-reset-mode-separation/valid-repeatable-demo-reset.json" \
  "${backup_restore_false_pass_repo}/docs/deployment/fixtures/demo-reset-mode-separation/backup-restore-claim.json"
assert_fails_with \
  "${backup_restore_false_pass_repo}" \
  "Invalid Phase 55.4 demo reset fixture state for backup-restore-claim.json: expected rejection"

forbidden_claim_repo="${workdir}/forbidden-claim"
create_valid_repo "${forbidden_claim_repo}"
printf '%s\n' "Demo reset may delete live records." \
  >>"${forbidden_claim_repo}/docs/deployment/demo-reset-mode-separation.md"
assert_fails_with \
  "${forbidden_claim_repo}" \
  "Forbidden Phase 55.4 demo reset claim: Demo reset may delete live records"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/demo-reset-mode-separation.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 55.4 demo reset contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 55.4 demo reset and mode separation contract."

echo "Phase 55.4 demo reset and mode separation negative and valid checks passed."
