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

## 5. Field Coverage Verification

The field coverage matrix below classifies the reviewed Windows semantic areas as required, optional, unavailable, intentionally deferred, or exception-path constrained without ambiguity.

| Semantic area | Coverage status | Evidence or exception path |
| ---- | ---- | ---- |
| Event classification and timestamp semantics | Required | Covered by the reviewed normalized fixtures for event.code, event.action, @timestamp, event.created, and event.ingested. |
| Source provenance including event channel, provider, and collector or agent identity | Required | Covered by event.provider, event.module, event.dataset, and aegisops.provenance.ingest_path in the reviewed normalized fixtures. |
| Host identity and asset references | Required | Covered by host.name, host.hostname, and related.hosts in the reviewed normalized fixtures. |
| Actor identity and target identity when present | Required with exception path | The missing-actor edge fixture documents that absent actor identity is a detection-ready blocker for actor-dependent detections but remains an allowed schema-reviewed exception path for fixture validation without fabricating user fields. |
| Logon session context, token or integrity details, and group references | Optional | Group references are covered by group.name in the privileged-group-addition fixture, while logon and token details are not required for this narrow review set. |
| Process lineage and command-line context | Intentionally deferred | Windows security records in this narrow fixture set do not yet provide reviewed process lineage evidence, so broader process-context validation remains future work before detection-ready approval. |
| Source and destination network context for remote access or lateral movement records | Unavailable | The reviewed administrative-security fixture set does not credibly supply remote network context and therefore cannot claim it without fabrication. |
| Related user, host, IP, and process correlation fields | Required derived coverage | related.user and related.hosts are present where supported, and related.ip or related.process are omitted because the reviewed source records do not credibly expose them. |
| AegisOps-specific provenance annotations under aegisops.* | Required derived coverage | Covered by aegisops.provenance.* and aegisops.validation.* in the normalized fixtures. |

## 6. Replay Fixture Plan

Replay fixtures are stored under `ingest/replay/windows-security-and-endpoint/normalized/`.

## 7. Known Gaps and Non-Goals

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
    '{"@timestamp":"2026-03-31T12:00:00Z","event.created":"2026-03-31T12:00:03Z","event.ingested":"2026-03-31T12:00:08Z","event.action":"member-added-to-local-group","event.code":"4732","event.provider":"Microsoft-Windows-Security-Auditing","event.module":"windows","event.dataset":"windows.security","host.name":"WS-ADMIN-01","host.hostname":"WS-ADMIN-01.corp.example.invalid","user.name":"svc_admin_ops","destination.user.name":"jdoe","group.name":"Administrators","related.user":["svc_admin_ops","jdoe"],"related.hosts":["WS-ADMIN-01"],"aegisops.provenance.ingest_path":"review/windows-forwarded-event","aegisops.provenance.parser_version":"review-fixture-v1"}' \
    '{"@timestamp":"2026-03-31T12:05:00Z","event.created":"2026-03-31T12:05:02Z","event.ingested":"2026-03-31T12:05:06Z","event.action":"audit-log-cleared","event.code":"1102","event.provider":"Microsoft-Windows-Eventlog","event.module":"windows","event.dataset":"windows.security","host.name":"WS-SEC-02","host.hostname":"WS-SEC-02.corp.example.invalid","user.name":"secops.tier2","related.user":["secops.tier2"],"related.hosts":["WS-SEC-02"],"aegisops.provenance.ingest_path":"review/windows-eventlog","aegisops.provenance.parser_version":"review-fixture-v1"}' \
    '{"@timestamp":"2026-03-31T12:10:00Z","event.created":"2026-03-31T12:10:04Z","event.ingested":"2026-03-31T12:10:08Z","event.action":"local-user-created","event.code":"4720","event.provider":"Microsoft-Windows-Security-Auditing","event.module":"windows","event.dataset":"windows.security","host.name":"WS-APP-07","host.hostname":"WS-APP-07.corp.example.invalid","user.name":"helpdesk_admin","destination.user.name":"svc_tempops","related.user":["helpdesk_admin","svc_tempops"],"related.hosts":["WS-APP-07"],"aegisops.provenance.ingest_path":"review/windows-eventlog","aegisops.provenance.parser_version":"review-fixture-v1"}' \
    >"${target}/ingest/replay/windows-security-and-endpoint/normalized/success.ndjson"

  printf '%s\n' \
    '{"event.created":"2026-03-31T12:11:03Z","event.ingested":"2026-03-31T12:11:07Z","aegisops.validation.case":"missing-actor","aegisops.validation.note":"Actor identity unavailable in reviewed source payload.","event.original":"local-user-created-missing-actor.json"}' \
    '{"event.created":"2026-03-31T12:00:15Z","event.ingested":"2026-03-31T12:00:45Z","aegisops.provenance.clock_quality":"forwarded-event-time-anomaly","aegisops.validation.case":"forwarded-time-anomaly","aegisops.validation.note":"Source event time and collector receipt time diverge materially.","event.original":"audit-log-cleared-forwarded-time-anomaly.json"}' \
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

missing_coverage_repo="${workdir}/missing-coverage"
create_repo "${missing_coverage_repo}"
write_valid_assets "${missing_coverage_repo}"
python3 - <<'PY' "${missing_coverage_repo}/docs/source-families/windows-security-and-endpoint/onboarding-package.md"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
start = text.index("## 5. Field Coverage Verification")
end = text.index("## 6. Replay Fixture Plan")
path.write_text(text[:start] + text[end:])
PY
git -C "${missing_coverage_repo}" add .
commit_fixture "${missing_coverage_repo}"
assert_fails_with "${missing_coverage_repo}" "Missing Windows onboarding package heading: ## 5. Field Coverage Verification"

echo "Windows source onboarding asset verifier tests passed."
