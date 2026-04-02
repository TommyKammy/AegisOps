#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-opensearch-index-template-placeholders.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/opensearch/index-templates"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
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

write_docs() {
  local target="$1"

  write_file "${target}" "docs/requirements-baseline.md" "### 7.4 OpenSearch Index Naming

Recommended patterns:

* \`aegisops-logs-windows-*\`
* \`aegisops-logs-linux-*\`
* \`aegisops-logs-network-*\`
* \`aegisops-logs-saas-*\`"

  write_file "${target}" "docs/contributor-naming-guide.md" "### OpenSearch Indexes

- \`aegisops-logs-windows-*\`
- \`aegisops-logs-linux-*\`
- \`aegisops-logs-network-*\`
- \`aegisops-logs-saas-*\`"
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
write_docs "${valid_repo}"
write_placeholders "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_template_repo="${workdir}/missing-template"
create_repo "${missing_template_repo}"
write_docs "${missing_template_repo}"
write_placeholders "${missing_template_repo}"
rm "${missing_template_repo}/opensearch/index-templates/aegisops-logs-saas-template.json"
git -C "${missing_template_repo}" add -u
commit_fixture "${missing_template_repo}"
assert_fails_with "${missing_template_repo}" "aegisops-logs-saas-template.json"

ilm_repo="${workdir}/ilm-placeholder"
create_repo "${ilm_repo}"
write_docs "${ilm_repo}"
write_placeholders "${ilm_repo}"
write_file "${ilm_repo}" "opensearch/index-templates/aegisops-logs-linux-template.json" "{
  \"index_patterns\": [
    \"aegisops-logs-linux-*\"
  ],
  \"template\": {
    \"settings\": {
      \"index.lifecycle.name\": \"logs-hot-warm\"
    }
  },
  \"_meta\": {
    \"description\": \"AegisOps linux log index template placeholder only. Not production-ready.\"
  }
}"
commit_fixture "${ilm_repo}"
assert_fails_with "${ilm_repo}" "must not define ILM behavior"

echo "verify-opensearch-index-template-placeholders tests passed"
