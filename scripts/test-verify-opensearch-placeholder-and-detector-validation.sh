#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-opensearch-placeholder-and-detector-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/opensearch/index-templates" "${target}/opensearch/detectors" "${target}/scripts"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
  cp "${repo_root}/scripts/verify-opensearch-index-template-placeholders.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-opensearch-detector-metadata-template.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-opensearch-placeholder-and-detector-validation.sh" "${target}/scripts/"
  chmod +x "${target}/scripts/"verify-opensearch-*.sh
}

write_file() {
  local target="$1"
  local path="$2"
  local content="$3"

  printf '%s\n' "${content}" >"${target}/${path}"
  git -C "${target}" add "${path}"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit -q -m "fixture"
}

write_baseline_docs() {
  local target="$1"

  write_file "${target}" "docs/requirements-baseline.md" "### OpenSearch Index Naming

- \`aegisops-logs-windows-*\`
- \`aegisops-logs-linux-*\`
- \`aegisops-logs-network-*\`
- \`aegisops-logs-saas-*\`"

  write_file "${target}" "docs/contributor-naming-guide.md" "### OpenSearch Indexes

- \`aegisops-logs-windows-*\`
- \`aegisops-logs-linux-*\`
- \`aegisops-logs-network-*\`
- \`aegisops-logs-saas-*\`

### Detectors

- \`aegisops-<source>-<use-case>-<severity>\`"

  write_file "${target}" "docs/repository-structure-baseline.md" "# AegisOps Repository Structure Baseline

- \`opensearch/\` stores OpenSearch configuration assets."
}

write_opensearch_docs() {
  local target="$1"

  write_file "${target}" "opensearch/index-templates/README.md" "# AegisOps OpenSearch Index Template Placeholders

Placeholder-only templates use the approved \`aegisops-logs-<family>-*\` naming baseline."

  write_file "${target}" "opensearch/detectors/README.md" "# AegisOps OpenSearch Detector Guidance

Tracked detector metadata should document expected behavior, MITRE ATT&CK technique tags, source prerequisites, and false-positive considerations."
}

write_placeholders() {
  local target="$1"

  for family in windows linux network saas; do
    write_file "${target}" "opensearch/index-templates/aegisops-logs-${family}-template.json" "{
  \"index_patterns\": [
    \"aegisops-logs-${family}-*\"
  ],
  \"template\": {},
  \"_meta\": {
    \"description\": \"AegisOps ${family} log index template placeholder only. Not production-ready.\"
  }
}"
  done
}

write_detector_template() {
  local target="$1"

  write_file "${target}" "opensearch/detectors/aegisops-detector-metadata-template.yaml" "# AegisOps detector metadata template only. Do not import as an active detector.
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
}

write_validation_doc() {
  local target="$1"

  write_file "${target}" "docs/opensearch-placeholder-and-detector-validation.md" "# OpenSearch Placeholder and Detector Validation

- Validation date: 2026-04-02
- Baseline references: \`docs/contributor-naming-guide.md\`, \`docs/requirements-baseline.md\`, \`docs/repository-structure-baseline.md\`, \`opensearch/index-templates/README.md\`, \`opensearch/detectors/README.md\`
- Verification commands: \`bash scripts/verify-opensearch-index-template-placeholders.sh\`, \`bash scripts/verify-opensearch-detector-metadata-template.sh\`, \`bash scripts/verify-opensearch-placeholder-and-detector-validation.sh\`
- Validation status: PASS

## Reviewed Artifacts

- \`opensearch/index-templates/README.md\`
- \`opensearch/index-templates/aegisops-logs-linux-template.json\`
- \`opensearch/index-templates/aegisops-logs-network-template.json\`
- \`opensearch/index-templates/aegisops-logs-saas-template.json\`
- \`opensearch/index-templates/aegisops-logs-windows-template.json\`
- \`opensearch/detectors/README.md\`
- \`opensearch/detectors/aegisops-detector-metadata-template.yaml\`

## Index Template Naming Review Result

The placeholder assets under \`opensearch/index-templates/\` use the approved \`aegisops-logs-<family>-*\` naming baseline for the current Windows, Linux, network, and SaaS log families.

## Detector Metadata Review Result

The detector metadata template remains placeholder-only and includes the required detector name pattern, owner, purpose, severity, expected behavior, MITRE ATT&CK technique tags, source prerequisites, and false-positive considerations.

## Deviations

No deviations found."
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
write_opensearch_docs "${valid_repo}"
write_placeholders "${valid_repo}"
write_detector_template "${valid_repo}"
write_validation_doc "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_report_repo="${workdir}/missing-report"
create_repo "${missing_report_repo}"
write_baseline_docs "${missing_report_repo}"
write_opensearch_docs "${missing_report_repo}"
write_placeholders "${missing_report_repo}"
write_detector_template "${missing_report_repo}"
commit_fixture "${missing_report_repo}"
assert_fails_with "${missing_report_repo}" "Missing OpenSearch placeholder and detector validation result document"

missing_artifact_repo="${workdir}/missing-artifact"
create_repo "${missing_artifact_repo}"
write_baseline_docs "${missing_artifact_repo}"
write_opensearch_docs "${missing_artifact_repo}"
write_placeholders "${missing_artifact_repo}"
write_detector_template "${missing_artifact_repo}"
write_validation_doc "${missing_artifact_repo}"
perl -0pi -e 's/^- `opensearch\/detectors\/README\.md`\n//m' \
  "${missing_artifact_repo}/docs/opensearch-placeholder-and-detector-validation.md"
git -C "${missing_artifact_repo}" add docs/opensearch-placeholder-and-detector-validation.md
commit_fixture "${missing_artifact_repo}"
assert_fails_with "${missing_artifact_repo}" "Validation document must list reviewed artifact: opensearch/detectors/README.md"

bad_result_repo="${workdir}/bad-result"
create_repo "${bad_result_repo}"
write_baseline_docs "${bad_result_repo}"
write_opensearch_docs "${bad_result_repo}"
write_placeholders "${bad_result_repo}"
write_detector_template "${bad_result_repo}"
write_validation_doc "${bad_result_repo}"
perl -0pi -e 's/The detector metadata template remains placeholder-only and includes the required detector name pattern, owner, purpose, severity, expected behavior, MITRE ATT&CK technique tags, source prerequisites, and false-positive considerations\./Detector metadata was checked./' \
  "${bad_result_repo}/docs/opensearch-placeholder-and-detector-validation.md"
git -C "${bad_result_repo}" add docs/opensearch-placeholder-and-detector-validation.md
commit_fixture "${bad_result_repo}"
assert_fails_with "${bad_result_repo}" "Missing validation statement in"

echo "verify-opensearch-placeholder-and-detector-validation tests passed"
