#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-6-opensearch-detector-artifacts.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p \
    "${target}/docs" \
    "${target}/opensearch/detectors/windows-security-and-endpoint" \
    "${target}/scripts" \
    "${target}/sigma/curated/windows-security-and-endpoint"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
  cp "${verifier}" "${target}/scripts/"
  chmod +x "${target}/scripts/verify-phase-6-opensearch-detector-artifacts.sh"
}

write_baseline_docs() {
  local target="$1"

  printf '%s\n' '# AegisOps Phase 6 Initial Telemetry Slice

## 1. Purpose

This document selects the single initial telemetry family and first detection use cases for the Phase 6 validated slice.

## 2. Selected Initial Telemetry Family

The selected initial telemetry family for the Phase 6 slice is Windows security and endpoint telemetry.

Phase 6 starts with one telemetry family only.

## 3. Selected Initial Detection Use Cases

The Phase 6 slice is limited to these three initial detection use cases:

1. Privileged group membership change
2. Audit log cleared
3. New local user created' >"${target}/docs/phase-6-initial-telemetry-slice.md"

  printf '%s\n' '# AegisOps Sigma-to-OpenSearch Translation Strategy

## 3. Supported Sigma Subset for the Approved Baseline

AegisOps supports only single-rule, single-event Sigma detections whose logic can be translated into reviewable OpenSearch detector content without changing the rule'"'"'s meaning.

## 6. OpenSearch-Native Fallback Path

When a detection requirement cannot be translated safely from the approved Sigma subset, the detection must remain OpenSearch-native and carry explicit documentation that Sigma is not the source of truth for that rule.' >"${target}/docs/sigma-to-opensearch-translation-strategy.md"
}

write_sigma_rules() {
  local target="$1"

  printf '%s\n' 'title: AegisOps Windows Privileged Group Membership Change
id: 2b6d9ef3-0e1e-4e42-a0c2-9f4f7f0d4c81
source_of_truth: sigma
severity: high' >"${target}/sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml"

  printf '%s\n' 'title: AegisOps Windows Audit Log Cleared
id: 4f5b2a71-91d4-4d75-85a1-c0fc12276fea
source_of_truth: sigma
severity: high' >"${target}/sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"

  printf '%s\n' 'title: AegisOps Windows New Local User Created
id: 91c9f67d-76f5-41f1-9ccf-66942a33df4f
source_of_truth: sigma
severity: medium' >"${target}/sigma/curated/windows-security-and-endpoint/new-local-user-created.yml"
}

write_detector_artifact() {
  local target="$1"
  local path="$2"
  local detector_name="$3"
  local sigma_path="$4"
  local sigma_rule_id="$5"
  local severity="$6"
  local query="$7"

  printf '%s\n' "artifact_kind: aegisops-opensearch-detector
artifact_version: v1
detector_name: ${detector_name}
status: staging
deployment_scope: staging-only
production_eligible: false
source_family: windows-security-and-endpoint
sigma_rule_path: ${sigma_path}
sigma_rule_id: ${sigma_rule_id}
source_of_truth: sigma
index_patterns:
  - aegisops-logs-windows-*
validation_target_index:
  - aegisops-logs-windows-staging-*
severity: ${severity}
query_language: lucene
query: ${query}
fallback_handling: No OpenSearch-native fallback is required for this supported single-event Sigma translation.
" >"${target}/${path}"
}

write_validation_doc() {
  local target="$1"

  printf '%s\n' '# Phase 6 OpenSearch Detector Artifact Validation

- Validation date: 2026-04-03
- Validation status: PASS

## Reviewed Artifacts

- `opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml`
- `opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml`
- `opensearch/detectors/windows-security-and-endpoint/new-local-user-created-staging.yaml`

## Review Result

The reviewed detector artifacts remain staging-only, preserve the selected Sigma rule identities, and limit validation to Windows staging indexes.

## Fallback Handling

No OpenSearch-native fallback is required for the selected Phase 6 slice because all three use cases remain within the approved single-event Sigma translation subset.' >"${target}/docs/phase-6-opensearch-detector-artifact-validation.md"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" add .
  git -C "${target}" commit -q -m "fixture"
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
write_baseline_docs "${valid_repo}"
write_sigma_rules "${valid_repo}"
write_detector_artifact \
  "${valid_repo}" \
  "opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml" \
  "aegisops-windows-privileged-group-membership-change-high" \
  "sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml" \
  "2b6d9ef3-0e1e-4e42-a0c2-9f4f7f0d4c81" \
  "high" \
  "'event.dataset:\"windows.security\" AND event.code:(4728 OR 4732 OR 4756) AND group.name:(\"Administrators\" OR \"Domain Admins\" OR \"Enterprise Admins\")'"
write_detector_artifact \
  "${valid_repo}" \
  "opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml" \
  "aegisops-windows-audit-log-cleared-high" \
  "sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml" \
  "4f5b2a71-91d4-4d75-85a1-c0fc12276fea" \
  "high" \
  "'event.dataset:\"windows.security\" AND event.code:1102 AND event.action:\"audit-log-cleared\"'"
write_detector_artifact \
  "${valid_repo}" \
  "opensearch/detectors/windows-security-and-endpoint/new-local-user-created-staging.yaml" \
  "aegisops-windows-new-local-user-created-medium" \
  "sigma/curated/windows-security-and-endpoint/new-local-user-created.yml" \
  "91c9f67d-76f5-41f1-9ccf-66942a33df4f" \
  "medium" \
  "'event.dataset:\"windows.security\" AND event.code:4720 AND event.action:\"local-user-created\"'"
write_validation_doc "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_artifact_repo="${workdir}/missing-artifact"
create_repo "${missing_artifact_repo}"
write_baseline_docs "${missing_artifact_repo}"
write_sigma_rules "${missing_artifact_repo}"
write_validation_doc "${missing_artifact_repo}"
commit_fixture "${missing_artifact_repo}"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 6 detector artifact: ${missing_artifact_repo}/opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml"

bad_scope_repo="${workdir}/bad-scope"
create_repo "${bad_scope_repo}"
write_baseline_docs "${bad_scope_repo}"
write_sigma_rules "${bad_scope_repo}"
write_detector_artifact \
  "${bad_scope_repo}" \
  "opensearch/detectors/windows-security-and-endpoint/privileged-group-membership-change-staging.yaml" \
  "aegisops-windows-privileged-group-membership-change-high" \
  "sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml" \
  "2b6d9ef3-0e1e-4e42-a0c2-9f4f7f0d4c81" \
  "high" \
  "'event.dataset:\"windows.security\" AND event.code:(4728 OR 4732 OR 4756) AND group.name:(\"Administrators\" OR \"Domain Admins\" OR \"Enterprise Admins\")'"
write_detector_artifact \
  "${bad_scope_repo}" \
  "opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml" \
  "aegisops-windows-audit-log-cleared-high" \
  "sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml" \
  "4f5b2a71-91d4-4d75-85a1-c0fc12276fea" \
  "high" \
  "'event.dataset:\"windows.security\" AND event.code:1102 AND event.action:\"audit-log-cleared\"'"
write_detector_artifact \
  "${bad_scope_repo}" \
  "opensearch/detectors/windows-security-and-endpoint/new-local-user-created-staging.yaml" \
  "aegisops-windows-new-local-user-created-medium" \
  "sigma/curated/windows-security-and-endpoint/new-local-user-created.yml" \
  "91c9f67d-76f5-41f1-9ccf-66942a33df4f" \
  "medium" \
  "'event.dataset:\"windows.security\" AND event.code:4720 AND event.action:\"local-user-created\"'"
write_validation_doc "${bad_scope_repo}"
perl -0pi -e 's/deployment_scope: staging-only/deployment_scope: production/' \
  "${bad_scope_repo}/opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml"
git -C "${bad_scope_repo}" add .
git -C "${bad_scope_repo}" commit -q -m "fixture"
assert_fails_with \
  "${bad_scope_repo}" \
  "Detector artifact must remain staging-only: ${bad_scope_repo}/opensearch/detectors/windows-security-and-endpoint/audit-log-cleared-staging.yaml"

echo "verify-phase-6-opensearch-detector-artifacts tests passed"
