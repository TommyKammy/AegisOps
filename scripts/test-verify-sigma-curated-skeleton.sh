#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-sigma-curated-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/sigma/curated/windows-security-and-endpoint"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_valid_curated_slice() {
  local target="$1"

  printf '%s\n' '# Sigma Curated Directory

Purpose: reviewed Sigma rules approved for AegisOps onboarding.

Status: candidate Windows security and endpoint rules for the selected Phase 6 use cases only.

Scope: privileged group membership change, audit log cleared, and new local user created.

These rules stay within the approved single-event Sigma subset and remain review content only.' >"${target}/sigma/curated/README.md"

  printf '%s\n' 'title: AegisOps Windows Privileged Group Membership Change
id: 2b6d9ef3-0e1e-4e42-a0c2-9f4f7f0d4c81
status: candidate
description: Reviewed candidate rule for the initial Windows Phase 6 use case.
owner: IT Operations, Information Systems Department
purpose: Detect a reviewed Windows event where a user is added to a privileged local or domain group.
expected_behavior: Create a reviewable finding when reviewed Windows telemetry records a membership change into a privileged group.
severity: high
level: high
required_reviewer: Security Engineering reviewer
expiry: 2026-07-01
source_of_truth: sigma
validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#privileged-group-membership-change
rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable.
tags:
  - attack.persistence
  - attack.privilege-escalation
  - attack.t1098
logsource:
  product: windows
  service: security
field_dependencies:
  - event.dataset
  - event.code
  - group.name
  - user.name
  - destination.user.name
source_prerequisites:
  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  - Required normalized fields event.dataset, event.code, group.name, user.name, and destination.user.name are preserved for reviewed success-path fixtures.
false_positive_considerations:
  - Approved administrative group changes by endpoint engineering, identity administrators, or build automation can legitimately match.
detection:
  selection:
    event.dataset: windows.security
    event.code:
      - '\''4728'\''
      - '\''4732'\''
      - '\''4756'\''
    group.name:
      - Administrators
      - Domain Admins
      - Enterprise Admins
  condition: selection' >"${target}/sigma/curated/windows-security-and-endpoint/privileged-group-membership-change.yml"

  printf '%s\n' 'title: AegisOps Windows Audit Log Cleared
id: 4f5b2a71-91d4-4d75-85a1-c0fc12276fea
status: candidate
description: Reviewed candidate rule for the initial Windows Phase 6 use case.
owner: IT Operations, Information Systems Department
purpose: Detect a reviewed Windows event that records clearing of the Windows audit log.
expected_behavior: Create a reviewable finding when reviewed Windows telemetry records audit-log-cleared activity.
severity: high
level: high
required_reviewer: Security Engineering reviewer
expiry: 2026-07-01
source_of_truth: sigma
validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#audit-log-cleared
rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable.
tags:
  - attack.defense-evasion
  - attack.t1070.001
logsource:
  product: windows
  service: security
field_dependencies:
  - event.dataset
  - event.code
  - event.action
  - host.name
  - user.name
source_prerequisites:
  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  - Required normalized fields event.dataset, event.code, event.action, host.name, and user.name are preserved for reviewed success-path fixtures.
false_positive_considerations:
  - Approved maintenance, forensic review, or controlled break-glass procedures can legitimately clear audit logs.
detection:
  selection:
    event.dataset: windows.security
    event.code: '\''1102'\''
    event.action: audit-log-cleared
  condition: selection' >"${target}/sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"

  printf '%s\n' 'title: AegisOps Windows New Local User Created
id: 91c9f67d-76f5-41f1-9ccf-66942a33df4f
status: candidate
description: Reviewed candidate rule for the initial Windows Phase 6 use case.
owner: IT Operations, Information Systems Department
purpose: Detect a reviewed Windows event where a new local user account is created on a managed host.
expected_behavior: Create a reviewable finding when reviewed Windows telemetry records local account creation.
severity: medium
level: medium
required_reviewer: Security Engineering reviewer
expiry: 2026-07-01
source_of_truth: sigma
validation_evidence_reference: ingest/replay/windows-security-and-endpoint/normalized/success.ndjson#new-local-user-created
rollback_expectation: Revert the translated detector content or return the rule to candidate review if validation volume or scope is unacceptable.
tags:
  - attack.persistence
  - attack.t1136.001
logsource:
  product: windows
  service: security
field_dependencies:
  - event.dataset
  - event.code
  - event.action
  - host.name
  - user.name
  - destination.user.name
source_prerequisites:
  - Windows security and endpoint telemetry family remains schema-reviewed under docs/source-families/windows-security-and-endpoint/onboarding-package.md.
  - Required normalized fields event.dataset, event.code, event.action, host.name, user.name, and destination.user.name are preserved for reviewed success-path fixtures.
false_positive_considerations:
  - Approved help desk provisioning, imaging workflows, or temporary break-glass account creation can legitimately match.
detection:
  selection:
    event.dataset: windows.security
    event.code: '\''4720'\''
    event.action: local-user-created
  condition: selection' >"${target}/sigma/curated/windows-security-and-endpoint/new-local-user-created.yml"
}

assert_passes() {
  local target="$1"
  if ! "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"
  if "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi
  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

passing_repo="${workdir}/passing"
create_repo "${passing_repo}"
write_valid_curated_slice "${passing_repo}"
assert_passes "${passing_repo}"

missing_rule_repo="${workdir}/missing-rule"
create_repo "${missing_rule_repo}"
write_valid_curated_slice "${missing_rule_repo}"
rm "${missing_rule_repo}/sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"
assert_fails_with \
  "${missing_rule_repo}" \
  "Missing curated Sigma rule: ${missing_rule_repo}/sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"

placeholder_repo="${workdir}/placeholder"
create_repo "${placeholder_repo}"
printf '%s\n' '# Sigma Curated Directory

Purpose: reviewed Sigma rules approved for AegisOps onboarding.

Status: placeholder only; no active Sigma detection rules are committed here yet.

Rule onboarding requires future review and explicit approval before any real rule content is added.' >"${placeholder_repo}/sigma/curated/README.md"
assert_fails_with \
  "${placeholder_repo}" \
  "Curated Sigma content does not match reviewed baseline: ${placeholder_repo}/sigma/curated/README.md"

unsupported_repo="${workdir}/unsupported"
create_repo "${unsupported_repo}"
write_valid_curated_slice "${unsupported_repo}"
python3 - <<'PY' "${unsupported_repo}/sigma/curated/windows-security-and-endpoint/new-local-user-created.yml"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace("condition: selection", "timeframe: 5m\ncondition: selection")
path.write_text(text)
PY
assert_fails_with \
  "${unsupported_repo}" \
  "Curated Sigma content does not match reviewed baseline: ${unsupported_repo}/sigma/curated/windows-security-and-endpoint/new-local-user-created.yml"

required_symlink_repo="${workdir}/required-symlink"
create_repo "${required_symlink_repo}"
write_valid_curated_slice "${required_symlink_repo}"
rm "${required_symlink_repo}/sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"
ln -s \
  "${required_symlink_repo}/sigma/curated/windows-security-and-endpoint/new-local-user-created.yml" \
  "${required_symlink_repo}/sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"
assert_fails_with \
  "${required_symlink_repo}" \
  "Curated Sigma rule must be a regular file: ${required_symlink_repo}/sigma/curated/windows-security-and-endpoint/audit-log-cleared.yml"

unexpected_repo="${workdir}/unexpected"
create_repo "${unexpected_repo}"
write_valid_curated_slice "${unexpected_repo}"
printf '%s\n' 'title: extra' >"${unexpected_repo}/sigma/curated/windows-security-and-endpoint/extra.yml"
assert_fails_with \
  "${unexpected_repo}" \
  "Unexpected curated Sigma content outside the selected Phase 6 slice."

extra_symlink_repo="${workdir}/extra-symlink"
create_repo "${extra_symlink_repo}"
write_valid_curated_slice "${extra_symlink_repo}"
printf '%s\n' 'title: off-slice' >"${extra_symlink_repo}/off-slice.yml"
ln -s \
  "${extra_symlink_repo}/off-slice.yml" \
  "${extra_symlink_repo}/sigma/curated/windows-security-and-endpoint/off-slice.yml"
assert_fails_with \
  "${extra_symlink_repo}" \
  "Curated Sigma content must not include symlinks."

echo "verify-sigma-curated-skeleton tests passed"
