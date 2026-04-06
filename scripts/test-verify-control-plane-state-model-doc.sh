#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-control-plane-state-model-doc.sh"
canonical_doc="${repo_root}/docs/control-plane-state-model.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_canonical_doc() {
  local target="$1"

  cp "${canonical_doc}" "${target}/docs/control-plane-state-model.md"
  git -C "${target}" add docs/control-plane-state-model.md
}

remove_text_from_doc() {
  local target="$1"
  local expected_text="$2"
  local doc_path="${target}/docs/control-plane-state-model.md"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${doc_path}"
  git -C "${target}" add docs/control-plane-state-model.md
}

replace_text_in_doc() {
  local target="$1"
  local old_text="$2"
  local new_text="$3"
  local doc_path="${target}/docs/control-plane-state-model.md"

  OLD_TEXT="${old_text}" NEW_TEXT="${new_text}" perl -0pi -e 's/\Q$ENV{OLD_TEXT}\E/$ENV{NEW_TEXT}/g' "${doc_path}"
  git -C "${target}" add docs/control-plane-state-model.md
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_canonical_doc "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

postgres_authoritative_repo="${workdir}/postgres-authoritative"
create_repo "${postgres_authoritative_repo}"
write_canonical_doc "${postgres_authoritative_repo}"
replace_text_in_doc \
  "${postgres_authoritative_repo}" \
  'No new live datastore rollout is approved in this phase. The current control-plane runtime remains `persistence_mode="in_memory"`, `postgres/control-plane/` remains the reviewed schema and migration home for future PostgreSQL-backed persistence work, and OpenSearch remains the analytics-plane store for telemetry and detection outputs.' \
  'The reviewed local control-plane runtime now reports `persistence_mode="postgresql"` and treats the PostgreSQL-backed control-plane store as the authoritative persistence path for local runtime and inspection flows, while `postgres/control-plane/` remains the reviewed schema and migration home and OpenSearch remains the analytics-plane store for telemetry and detection outputs.'
commit_fixture "${postgres_authoritative_repo}"
assert_passes "${postgres_authoritative_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing control-plane state model document:"

missing_reconciliation_repo="${workdir}/missing-reconciliation"
create_repo "${missing_reconciliation_repo}"
write_canonical_doc "${missing_reconciliation_repo}"
remove_text_from_doc "${missing_reconciliation_repo}" "The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed."
commit_fixture "${missing_reconciliation_repo}"
assert_fails_with "${missing_reconciliation_repo}" "The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed."

missing_idempotency_repo="${workdir}/missing-idempotency"
create_repo "${missing_idempotency_repo}"
write_canonical_doc "${missing_idempotency_repo}"
remove_text_from_doc "${missing_idempotency_repo}" "Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays."
commit_fixture "${missing_idempotency_repo}"
assert_fails_with "${missing_idempotency_repo}" "Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays."

missing_ownership_split_repo="${workdir}/missing-ownership-split"
create_repo "${missing_ownership_split_repo}"
write_canonical_doc "${missing_ownership_split_repo}"
remove_text_from_doc "${missing_ownership_split_repo}" "The approved ownership split for the reviewed PostgreSQL-backed boundary is:"
commit_fixture "${missing_ownership_split_repo}"
assert_fails_with "${missing_ownership_split_repo}" "The approved ownership split for the reviewed PostgreSQL-backed boundary is:"

missing_evidence_withdrawn_state_repo="${workdir}/missing-evidence-withdrawn-state"
create_repo "${missing_evidence_withdrawn_state_repo}"
write_canonical_doc "${missing_evidence_withdrawn_state_repo}"
remove_text_from_doc "${missing_evidence_withdrawn_state_repo}" '| `withdrawn` | The evidence remains historically visible, but it must no longer be relied on because provenance, integrity, or scope was invalidated. |'
commit_fixture "${missing_evidence_withdrawn_state_repo}"
assert_fails_with "${missing_evidence_withdrawn_state_repo}" '| `withdrawn` | The evidence remains historically visible, but it must no longer be relied on because provenance, integrity, or scope was invalidated. |'

missing_reconciliation_record_repo="${workdir}/missing-reconciliation-record"
create_repo "${missing_reconciliation_record_repo}"
write_canonical_doc "${missing_reconciliation_record_repo}"
remove_text_from_doc "${missing_reconciliation_record_repo}" '| `Reconciliation` | AegisOps control-plane reconciliation record | Cross-system linkage, mismatch tracking, and resolution state must not dissolve into alert fields, case notes, or n8n metadata. |'
commit_fixture "${missing_reconciliation_record_repo}"
assert_fails_with "${missing_reconciliation_record_repo}" '| `Reconciliation` | AegisOps control-plane reconciliation record | Cross-system linkage, mismatch tracking, and resolution state must not dissolve into alert fields, case notes, or n8n metadata. |'

missing_substrate_signal_repo="${workdir}/missing-substrate-signal"
create_repo "${missing_substrate_signal_repo}"
write_canonical_doc "${missing_substrate_signal_repo}"
remove_text_from_doc "${missing_substrate_signal_repo}" '| `Substrate Detection Record` | Approved upstream detection substrate | The detection substrate remains the system of record for substrate-native detection, correlation, and alerting artifacts plus their native identifiers. |'
commit_fixture "${missing_substrate_signal_repo}"
assert_fails_with "${missing_substrate_signal_repo}" '| `Substrate Detection Record` | Approved upstream detection substrate | The detection substrate remains the system of record for substrate-native detection, correlation, and alerting artifacts plus their native identifiers. |'

stale_pre_runtime_repo="${workdir}/stale-pre-runtime"
create_repo "${stale_pre_runtime_repo}"
write_canonical_doc "${stale_pre_runtime_repo}"
printf '%s\n' "This document defines the approved baseline control-plane state model for AegisOps before any dedicated control service or datastore is implemented." >> "${stale_pre_runtime_repo}/docs/control-plane-state-model.md"
git -C "${stale_pre_runtime_repo}" add docs/control-plane-state-model.md
commit_fixture "${stale_pre_runtime_repo}"
assert_fails_with "${stale_pre_runtime_repo}" "Forbidden control-plane state model statement still present: This document defines the approved baseline control-plane state model for AegisOps before any dedicated control service or datastore is implemented."

stale_future_control_layer_repo="${workdir}/stale-future-control-layer"
create_repo "${stale_future_control_layer_repo}"
write_canonical_doc "${stale_future_control_layer_repo}"
printf '%s\n' "The future AegisOps control layer is responsible for:" >> "${stale_future_control_layer_repo}/docs/control-plane-state-model.md"
git -C "${stale_future_control_layer_repo}" add docs/control-plane-state-model.md
commit_fixture "${stale_future_control_layer_repo}"
assert_fails_with "${stale_future_control_layer_repo}" "Forbidden control-plane state model statement still present: The future AegisOps control layer is responsible for:"

stale_future_control_record_repo="${workdir}/stale-future-control-record"
create_repo "${stale_future_control_record_repo}"
write_canonical_doc "${stale_future_control_record_repo}"
printf '%s\n' "Reconciliation must preserve auditable disagreement. When OpenSearch, n8n, and the future control record disagree, the platform must retain that mismatch as an explicit state that operators can inspect and resolve rather than overwriting one side to make the data look clean." >> "${stale_future_control_record_repo}/docs/control-plane-state-model.md"
git -C "${stale_future_control_record_repo}" add docs/control-plane-state-model.md
commit_fixture "${stale_future_control_record_repo}"
assert_fails_with "${stale_future_control_record_repo}" "Forbidden control-plane state model statement still present: Reconciliation must preserve auditable disagreement. When OpenSearch, n8n, and the future control record disagree, the platform must retain that mismatch as an explicit state that operators can inspect and resolve rather than overwriting one side to make the data look clean."

echo "Control-plane state model verifier enforces required policy statements."
