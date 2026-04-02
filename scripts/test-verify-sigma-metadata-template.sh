#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-sigma-metadata-template.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/sigma"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_template() {
  local target="$1"
  local content="$2"

  printf '%s\n' "${content}" >"${target}/sigma/aegisops-sigma-metadata-template.yml"
  git -C "${target}" add sigma/aegisops-sigma-metadata-template.yml
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
write_template "${valid_repo}" "# AegisOps Sigma metadata template only. Do not promote as a real Sigma rule.
title: AegisOps Sigma Metadata Template
id: <placeholder-uuid>
status: experimental
description: Placeholder-only metadata scaffold for future curated Sigma rule onboarding.
template_kind: aegisops-sigma-rule-metadata
template_status: placeholder-only
owner: <team-or-role>
purpose: <what this rule is intended to detect>
expected_behavior: <what analysts should expect when this rule matches>
severity: <low|medium|high|critical>
tags:
  - attack.<tactic-or-technique>
logsource:
  product: <required log source product>
  service: <required log source service or subtype>
source_prerequisites:
  - <required log source, retention, field, or normalization dependency>
detection:
  placeholder: metadata-only
  condition: placeholder
governance:
  activation_policy: metadata-only template; no active Sigma rule logic is introduced from this file
  baseline_references:
    - docs/requirements-baseline.md
    - docs/repository-structure-baseline.md"
assert_passes "${valid_repo}"

missing_file_repo="${workdir}/missing-file"
create_repo "${missing_file_repo}"
git -C "${missing_file_repo}" commit -q --allow-empty -m "fixture"
assert_fails_with "${missing_file_repo}" "Missing Sigma metadata template"

missing_field_repo="${workdir}/missing-field"
create_repo "${missing_field_repo}"
write_template "${missing_field_repo}" "# AegisOps Sigma metadata template only. Do not promote as a real Sigma rule.
title: AegisOps Sigma Metadata Template
id: <placeholder-uuid>
status: experimental
description: Placeholder-only metadata scaffold for future curated Sigma rule onboarding.
template_kind: aegisops-sigma-rule-metadata
template_status: placeholder-only
owner: <team-or-role>
purpose: <what this rule is intended to detect>
severity: <low|medium|high|critical>
tags:
  - attack.<tactic-or-technique>
logsource:
  product: <required log source product>
  service: <required log source service or subtype>
source_prerequisites:
  - <required log source, retention, field, or normalization dependency>
detection:
  placeholder: metadata-only
  condition: placeholder
governance:
  activation_policy: metadata-only template; no active Sigma rule logic is introduced from this file
  baseline_references:
    - docs/requirements-baseline.md
    - docs/repository-structure-baseline.md"
assert_fails_with "${missing_field_repo}" "expected_behavior"

logic_repo="${workdir}/logic"
create_repo "${logic_repo}"
write_template "${logic_repo}" "# AegisOps Sigma metadata template only. Do not promote as a real Sigma rule.
title: AegisOps Sigma Metadata Template
id: <placeholder-uuid>
status: experimental
description: Placeholder-only metadata scaffold for future curated Sigma rule onboarding.
template_kind: aegisops-sigma-rule-metadata
template_status: placeholder-only
owner: <team-or-role>
purpose: <what this rule is intended to detect>
expected_behavior: <what analysts should expect when this rule matches>
severity: <low|medium|high|critical>
tags:
  - attack.<tactic-or-technique>
logsource:
  product: <required log source product>
  service: <required log source service or subtype>
source_prerequisites:
  - <required log source, retention, field, or normalization dependency>
detection:
  placeholder: metadata-only
  selection:
    EventID: 4624
  condition: placeholder
governance:
  activation_policy: metadata-only template; no active Sigma rule logic is introduced from this file
  baseline_references:
    - docs/requirements-baseline.md
    - docs/repository-structure-baseline.md"
assert_fails_with "${logic_repo}" "must not include real rule logic"

echo "Sigma metadata template verifier tests passed."
