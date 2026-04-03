#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
curated_dir="${repo_root}/sigma/curated"
readme_path="${curated_dir}/README.md"
windows_dir="${curated_dir}/windows-security-and-endpoint"

expected_entries=(
  "${readme_path}"
  "${windows_dir}/audit-log-cleared.yml"
  "${windows_dir}/new-local-user-created.yml"
  "${windows_dir}/privileged-group-membership-change.yml"
)

required_readme_markers=(
  "Purpose: reviewed Sigma rules approved for AegisOps onboarding."
  "Status: candidate Windows security and endpoint rules for the selected Phase 6 use cases only."
  "Scope: privileged group membership change, audit log cleared, and new local user created."
  "These rules stay within the approved single-event Sigma subset and remain review content only."
)

assert_contains() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fq "${expected}" "${file_path}"; then
    echo "Missing required Sigma content in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

assert_not_contains() {
  local file_path="$1"
  local unexpected="$2"

  if grep -Fq "${unexpected}" "${file_path}"; then
    echo "Unsupported Sigma content in ${file_path}: ${unexpected}" >&2
    exit 1
  fi
}

verify_rule() {
  local file_path="$1"
  shift

  if [[ ! -f "${file_path}" ]]; then
    echo "Missing curated Sigma rule: ${file_path}" >&2
    exit 1
  fi

  while (( "$#" > 0 )); do
    assert_contains "${file_path}" "$1"
    shift
  done

  local unsupported_patterns=(
    "timeframe:"
    "count("
    "near"
    "|contains|all"
    "|re"
    "|cidr"
    "1 of "
    "all of "
  )

  local pattern
  for pattern in "${unsupported_patterns[@]}"; do
    assert_not_contains "${file_path}" "${pattern}"
  done
}

if [[ ! -d "${curated_dir}" ]]; then
  echo "Missing sigma curated directory: ${curated_dir}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing curated Sigma README: ${readme_path}" >&2
  exit 1
fi

for marker in "${required_readme_markers[@]}"; do
  assert_contains "${readme_path}" "${marker}"
done

verify_rule \
  "${windows_dir}/privileged-group-membership-change.yml" \
  "title: AegisOps Windows Privileged Group Membership Change" \
  "id: 2b6d9ef3-0e1e-4e42-a0c2-9f4f7f0d4c81" \
  "status: candidate" \
  "owner: IT Operations, Information Systems Department" \
  "purpose: Detect a reviewed Windows event where a user is added to a privileged local or domain group." \
  "severity: high" \
  "level: high" \
  "source_of_truth: sigma" \
  "required_reviewer: Security Engineering reviewer" \
  "expiry: 2026-07-01" \
  "validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#privileged-group-membership-change" \
  "rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable." \
  "event.dataset: windows.security" \
  "event.code:" \
  "  - '4728'" \
  "  - '4732'" \
  "  - '4756'" \
  "group.name:" \
  "  - Administrators" \
  "  - Domain Admins" \
  "  - Enterprise Admins" \
  "condition: selection" \
  "field_dependencies:" \
  "  - event.dataset" \
  "  - event.code" \
  "  - group.name" \
  "  - user.name" \
  "  - destination.user.name" \
  "source_prerequisites:" \
  "  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md." \
  "  - Required normalized fields event.dataset, event.code, group.name, user.name, and destination.user.name are preserved for reviewed success-path fixtures." \
  "false_positive_considerations:" \
  "  - Approved administrative group changes by endpoint engineering, identity administrators, or build automation can legitimately match."

verify_rule \
  "${windows_dir}/audit-log-cleared.yml" \
  "title: AegisOps Windows Audit Log Cleared" \
  "id: 4f5b2a71-91d4-4d75-85a1-c0fc12276fea" \
  "status: candidate" \
  "owner: IT Operations, Information Systems Department" \
  "purpose: Detect a reviewed Windows event that records clearing of the Windows audit log." \
  "severity: high" \
  "level: high" \
  "source_of_truth: sigma" \
  "required_reviewer: Security Engineering reviewer" \
  "expiry: 2026-07-01" \
  "validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#audit-log-cleared" \
  "rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable." \
  "event.dataset: windows.security" \
  "event.code: '1102'" \
  "event.action: audit-log-cleared" \
  "condition: selection" \
  "field_dependencies:" \
  "  - event.dataset" \
  "  - event.code" \
  "  - event.action" \
  "  - host.name" \
  "  - user.name" \
  "source_prerequisites:" \
  "  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md." \
  "  - Required normalized fields event.dataset, event.code, event.action, host.name, and user.name are preserved for reviewed success-path fixtures." \
  "false_positive_considerations:" \
  "  - Approved maintenance, forensic review, or controlled break-glass procedures can legitimately clear audit logs."

verify_rule \
  "${windows_dir}/new-local-user-created.yml" \
  "title: AegisOps Windows New Local User Created" \
  "id: 91c9f67d-76f5-41f1-9ccf-66942a33df4f" \
  "status: candidate" \
  "owner: IT Operations, Information Systems Department" \
  "purpose: Detect a reviewed Windows event where a new local user account is created on a managed host." \
  "severity: medium" \
  "level: medium" \
  "source_of_truth: sigma" \
  "required_reviewer: Security Engineering reviewer" \
  "expiry: 2026-07-01" \
  "validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#new-local-user-created" \
  "rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable." \
  "event.dataset: windows.security" \
  "event.code: '4720'" \
  "event.action: local-user-created" \
  "condition: selection" \
  "field_dependencies:" \
  "  - event.dataset" \
  "  - event.code" \
  "  - event.action" \
  "  - host.name" \
  "  - user.name" \
  "  - destination.user.name" \
  "source_prerequisites:" \
  "  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md." \
  "  - Required normalized fields event.dataset, event.code, event.action, host.name, user.name, and destination.user.name are preserved for reviewed success-path fixtures." \
  "false_positive_considerations:" \
  "  - Approved help desk provisioning, imaging workflows, or temporary break-glass account creation can legitimately match."

unexpected_entries=()
while IFS= read -r path; do
  match_found=0
  for expected in "${expected_entries[@]}"; do
    if [[ "${path}" == "${expected}" ]]; then
      match_found=1
      break
    fi
  done

  if [[ "${match_found}" -eq 0 ]]; then
    unexpected_entries+=("${path}")
  fi
done < <(find "${curated_dir}" -type f | LC_ALL=C sort)

if (( ${#unexpected_entries[@]} > 0 )); then
  echo "Unexpected curated Sigma content outside the selected Phase 6 slice." >&2
  printf ' %s\n' "${unexpected_entries[@]}" >&2
  exit 1
fi

echo "Curated Sigma rules and metadata are present for the selected Windows Phase 6 use cases."
