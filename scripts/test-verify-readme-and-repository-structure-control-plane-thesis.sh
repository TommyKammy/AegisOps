#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-readme-and-repository-structure-control-plane-thesis.sh"

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

write_valid_docs() {
  local target="$1"

  cat <<'EOF' > "${target}/README.md"
# AegisOps

**AegisOps** is a governed SecOps control plane above external detection and automation substrates.

Current scope:

- Platform baseline definition
- Architecture design and operating guidance
- Repository scaffolding
- Parameter catalog structure
- Implementation guardrails for AI-assisted development

- **OpenSearch** — optional or transitional analytics substrate, not the product core
- **Sigma** — optional or transitional rule-definition format or translation source, not the product core
- **n8n** — optional, transitional, or experimental orchestration substrate, not the product core
- **Control Plane Runtime** — future authoritative AegisOps service boundary for platform state and reconciliation

OpenSearch, Sigma, and n8n remain repository-tracked assets, but they are subordinate to the approved control-plane thesis and must not redefine the product narrative around themselves.

The current top-level tree still includes older substrate-specific directories and should be treated as transitional until a later ADR approves any substrate-specific repository rebaseline.
EOF

  cat <<'EOF' > "${target}/docs/repository-structure-baseline.md"
# AegisOps Repository Structure Baseline

This document intentionally defines the approved top-level repository layout and the purpose of each entry.

The current top-level structure remains transitional because it still reflects earlier repository phases and substrate-specific directory ownership.

Until a later ADR approves a repository rebaseline, contributors must treat the existing top-level tree as the reviewed baseline even where it does not yet match the long-term control-plane thesis.

| Path | Purpose |
| ---- | ------- |
| `opensearch/` | Transitional or optional OpenSearch repository assets such as compose definitions, detectors, templates, ILM policies, and snapshot-related configuration. Their presence does not make OpenSearch the product core. |
| `sigma/` | Transitional or optional Sigma repository assets, including reviewed rules, curated subsets, suppressions, field mappings, and placeholder markers that keep approved onboarding paths explicit before real rule content is added. Their presence does not make Sigma the product core. |
| `n8n/` | Transitional, optional, or experimental n8n workflow assets, approval patterns, credential templates, and webhook contract definitions. Their presence does not make n8n the product core or authority surface. |
| `control-plane/` | Live AegisOps control-plane application code, service bootstrapping, adapters, tests, and service-local documentation for the approved runtime boundary. |

- This document defines structure only and does not authorize runtime, deployment, or workflow implementation.
EOF

  git -C "${target}" add README.md docs/repository-structure-baseline.md
}

replace_text_in_doc() {
  local target="$1"
  local path="$2"
  local from_text="$3"
  local to_text="$4"

  FROM_TEXT="${from_text}" TO_TEXT="${to_text}" perl -0pi -e 's/\Q$ENV{FROM_TEXT}\E/$ENV{TO_TEXT}/g' "${target}/${path}"
  git -C "${target}" add "${path}"
}

remove_text_from_doc() {
  local target="$1"
  local path="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${target}/${path}"
  git -C "${target}" add "${path}"
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

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_valid_docs "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_readme_phrase_repo="${workdir}/missing-readme-phrase"
create_repo "${missing_readme_phrase_repo}"
write_valid_docs "${missing_readme_phrase_repo}"
remove_text_from_doc "${missing_readme_phrase_repo}" "README.md" "OpenSearch, Sigma, and n8n remain repository-tracked assets, but they are subordinate to the approved control-plane thesis and must not redefine the product narrative around themselves."
commit_fixture "${missing_readme_phrase_repo}"
assert_fails_with "${missing_readme_phrase_repo}" "Missing README control-plane thesis statement: OpenSearch, Sigma, and n8n remain repository-tracked assets, but they are subordinate to the approved control-plane thesis and must not redefine the product narrative around themselves."

legacy_readme_repo="${workdir}/legacy-readme"
create_repo "${legacy_readme_repo}"
write_valid_docs "${legacy_readme_repo}"
replace_text_in_doc "${legacy_readme_repo}" "README.md" "**AegisOps** is a governed SecOps control plane above external detection and automation substrates." "**AegisOps** is a governed SecOps control plane above external detection and automation substrates.\n\n**AegisOps** is an internal SOC + SOAR platform blueprint designed for flexible deployment across on-premise infrastructure and cloud environments, including AWS and other providers."
commit_fixture "${legacy_readme_repo}"
assert_fails_with "${legacy_readme_repo}" "Forbidden legacy README statement present: **AegisOps** is an internal SOC + SOAR platform blueprint designed for flexible deployment across on-premise infrastructure and cloud environments, including AWS and other providers."

missing_structure_phrase_repo="${workdir}/missing-structure-phrase"
create_repo "${missing_structure_phrase_repo}"
write_valid_docs "${missing_structure_phrase_repo}"
remove_text_from_doc "${missing_structure_phrase_repo}" "docs/repository-structure-baseline.md" "The current top-level structure remains transitional because it still reflects earlier repository phases and substrate-specific directory ownership."
commit_fixture "${missing_structure_phrase_repo}"
assert_fails_with "${missing_structure_phrase_repo}" "Missing repository structure thesis statement: The current top-level structure remains transitional because it still reflects earlier repository phases and substrate-specific directory ownership."

echo "README and repository structure verifier enforces the governed control-plane thesis."
