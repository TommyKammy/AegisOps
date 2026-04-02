#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-opensearch-detector-metadata-template.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/opensearch/detectors"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_template() {
  local target="$1"
  local content="$2"

  printf '%s\n' "${content}" >"${target}/opensearch/detectors/aegisops-detector-metadata-template.yaml"
  git -C "${target}" add opensearch/detectors/aegisops-detector-metadata-template.yaml
  git -C "${target}" commit -q -m "fixture"
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

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_template "${valid_repo}" "# AegisOps detector metadata template only. Do not import as an active detector.
template_kind: aegisops-detector-metadata
template_status: placeholder-only
detector_name: aegisops-<source>-<use-case>-<severity>
owner: <team-or-role>
purpose: <what this detector is intended to identify>
severity: <low|medium|high|critical>
expected_behavior: <what analysts should expect when this detector matches>
mitre_attack_technique_tags:
  - <technique-id-or-tag>
source_prerequisites:
  - <required log source, index pattern, or field dependency>
false_positive_considerations:
  - <known benign pattern, expected exception, or triage note>
governance:
  activation_policy: metadata-only template; no active detector is introduced from this file
  baseline_references:
    - docs/requirements-baseline.md
    - docs/contributor-naming-guide.md
    - docs/repository-structure-baseline.md"
assert_passes "${valid_repo}"

missing_file_repo="${workdir}/missing-file"
create_repo "${missing_file_repo}"
git -C "${missing_file_repo}" commit -q --allow-empty -m "fixture"
assert_fails_with "${missing_file_repo}" "Missing OpenSearch detector metadata template"

missing_field_repo="${workdir}/missing-field"
create_repo "${missing_field_repo}"
write_template "${missing_field_repo}" "# AegisOps detector metadata template only. Do not import as an active detector.
template_kind: aegisops-detector-metadata
template_status: placeholder-only
detector_name: aegisops-<source>-<use-case>-<severity>
owner: <team-or-role>
purpose: <what this detector is intended to identify>
severity: <low|medium|high|critical>
source_prerequisites:
  - <required log source, index pattern, or field dependency>
governance:
  activation_policy: metadata-only template; no active detector is introduced from this file
  baseline_references:
    - docs/requirements-baseline.md
    - docs/contributor-naming-guide.md
    - docs/repository-structure-baseline.md"
assert_fails_with "${missing_field_repo}" "expected_behavior"

missing_mitre_repo="${workdir}/missing-mitre"
create_repo "${missing_mitre_repo}"
write_template "${missing_mitre_repo}" "# AegisOps detector metadata template only. Do not import as an active detector.
template_kind: aegisops-detector-metadata
template_status: placeholder-only
detector_name: aegisops-<source>-<use-case>-<severity>
owner: <team-or-role>
purpose: <what this detector is intended to identify>
severity: <low|medium|high|critical>
expected_behavior: <what analysts should expect when this detector matches>
source_prerequisites:
  - <required log source, index pattern, or field dependency>
false_positive_considerations:
  - <known benign pattern, expected exception, or triage note>
governance:
  activation_policy: metadata-only template; no active detector is introduced from this file
  baseline_references:
    - docs/requirements-baseline.md
    - docs/contributor-naming-guide.md
    - docs/repository-structure-baseline.md"
assert_fails_with "${missing_mitre_repo}" "mitre_attack_technique_tags"

missing_false_positive_repo="${workdir}/missing-false-positive"
create_repo "${missing_false_positive_repo}"
write_template "${missing_false_positive_repo}" "# AegisOps detector metadata template only. Do not import as an active detector.
template_kind: aegisops-detector-metadata
template_status: placeholder-only
detector_name: aegisops-<source>-<use-case>-<severity>
owner: <team-or-role>
purpose: <what this detector is intended to identify>
severity: <low|medium|high|critical>
expected_behavior: <what analysts should expect when this detector matches>
mitre_attack_technique_tags:
  - <technique-id-or-tag>
source_prerequisites:
  - <required log source, index pattern, or field dependency>
governance:
  activation_policy: metadata-only template; no active detector is introduced from this file
  baseline_references:
    - docs/requirements-baseline.md
    - docs/contributor-naming-guide.md
    - docs/repository-structure-baseline.md"
assert_fails_with "${missing_false_positive_repo}" "false_positive_considerations"

runnable_repo="${workdir}/runnable"
create_repo "${runnable_repo}"
write_template "${runnable_repo}" "# AegisOps detector metadata template only. Do not import as an active detector.
template_kind: aegisops-detector-metadata
template_status: placeholder-only
detector_name: aegisops-<source>-<use-case>-<severity>
owner: <team-or-role>
purpose: <what this detector is intended to identify>
severity: <low|medium|high|critical>
expected_behavior: <what analysts should expect when this detector matches>
mitre_attack_technique_tags:
  - <technique-id-or-tag>
source_prerequisites:
  - <required log source, index pattern, or field dependency>
false_positive_considerations:
  - <known benign pattern, expected exception, or triage note>
enabled: false
governance:
  activation_policy: metadata-only template; no active detector is introduced from this file
  baseline_references:
    - docs/requirements-baseline.md
    - docs/contributor-naming-guide.md
    - docs/repository-structure-baseline.md"
assert_fails_with "${runnable_repo}" "must not include runnable detector content"

echo "OpenSearch detector metadata template verifier tests passed."
