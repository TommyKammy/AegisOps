#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-windows-source-onboarding-assets.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs/source-families/windows-security-and-endpoint"
  mkdir -p "${target}/ingest/replay/windows-security-and-endpoint/raw"
  mkdir -p "${target}/ingest/replay/windows-security-and-endpoint/normalized"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_valid_assets() {
  local target="$1"

  printf '%s\n' '# Windows Security and Endpoint Telemetry Onboarding Package

## 1. Family Scope and Readiness State

Readiness state: `schema-reviewed`

The selected telemetry family for the Phase 6 slice is Windows security and endpoint telemetry.

This package does not approve live source enrollment, credential onboarding, parser deployment, or detector activation.

## 2. Parser Ownership and Lifecycle Boundary

Parser ownership remains with IT Operations, Information Systems Department.

## 3. Raw Payload References

Representative raw payload references are stored under `ingest/replay/windows-security-and-endpoint/raw/`.

The reviewed success-path references in this package cover privileged group membership change, audit log cleared, and new local user created records.

The reviewed edge-case references in this package cover missing actor identity and forwarded-event timestamp caveats.

## 4. Normalization Mapping Summary

The mapping summary aligns raw Windows event fields to the canonical telemetry schema baseline.

## 5. Replay Fixture Plan

Replay fixtures are stored under `ingest/replay/windows-security-and-endpoint/normalized/`.

## 6. Known Gaps and Non-Goals

No live rollout is included in this review package.' >"${target}/docs/source-families/windows-security-and-endpoint/onboarding-package.md"

  printf '%s\n' '# Windows Security and Endpoint Replay Fixtures

These fixtures are review artifacts only.

The normal fixture set preserves representative success-path records for the initial Phase 6 Windows use cases.

The edge fixture set preserves records with missing actor context or timestamp caveats that future parser validation must handle explicitly.

All fixtures in this directory are synthetic or redacted review examples and are not approvals for live source onboarding.' >"${target}/ingest/replay/windows-security-and-endpoint/README.md"

  printf '%s\n' '{"EventID":4732}' >"${target}/ingest/replay/windows-security-and-endpoint/raw/privileged-group-addition.json"
  printf '%s\n' '{"EventID":1102}' >"${target}/ingest/replay/windows-security-and-endpoint/raw/audit-log-cleared.json"
  printf '%s\n' '{"EventID":4720}' >"${target}/ingest/replay/windows-security-and-endpoint/raw/local-user-created.json"
  printf '%s\n' '{"EventID":4720,"SubjectUserName":"-"}' >"${target}/ingest/replay/windows-security-and-endpoint/raw/local-user-created-missing-actor.json"
  printf '%s\n' '{"EventID":1102,"ForwardedTimeSkewSeconds":95}' >"${target}/ingest/replay/windows-security-and-endpoint/raw/audit-log-cleared-forwarded-time-anomaly.json"

  printf '%s\n' \
    '{"event.code":"4732"}' \
    '{"event.code":"1102"}' \
    '{"event.code":"4720"}' \
    >"${target}/ingest/replay/windows-security-and-endpoint/normalized/success.ndjson"

  printf '%s\n' \
    '{"aegisops.validation.case":"missing-actor"}' \
    '{"aegisops.validation.case":"forwarded-time-anomaly"}' \
    >"${target}/ingest/replay/windows-security-and-endpoint/normalized/edge.ndjson"

  git -C "${target}" add .
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
write_valid_assets "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Windows source onboarding package:"

missing_edge_repo="${workdir}/missing-edge"
create_repo "${missing_edge_repo}"
write_valid_assets "${missing_edge_repo}"
rm "${missing_edge_repo}/ingest/replay/windows-security-and-endpoint/raw/audit-log-cleared-forwarded-time-anomaly.json"
git -C "${missing_edge_repo}" add -A
commit_fixture "${missing_edge_repo}"
assert_fails_with "${missing_edge_repo}" "Missing Windows onboarding asset:"

missing_tag_repo="${workdir}/missing-tag"
create_repo "${missing_tag_repo}"
write_valid_assets "${missing_tag_repo}"
printf '%s\n' '{"aegisops.validation.case":"missing-actor"}' >"${missing_tag_repo}/ingest/replay/windows-security-and-endpoint/normalized/edge.ndjson"
git -C "${missing_tag_repo}" add .
commit_fixture "${missing_tag_repo}"
assert_fails_with "${missing_tag_repo}" "Missing edge fixture tagged for forwarded timestamp handling."

echo "Windows source onboarding asset verifier tests passed."
