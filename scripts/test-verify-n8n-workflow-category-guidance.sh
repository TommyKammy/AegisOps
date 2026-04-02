#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-n8n-workflow-category-guidance.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/n8n/workflows"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
}

write_valid_doc() {
  local target="$1"

  cat >"${target}/n8n/workflows/README.md" <<'EOF'
# AegisOps n8n Workflow Category Guidance

This document explains the approved purpose and current boundaries of the tracked n8n workflow categories in AegisOps.

## 1. Purpose

This directory exists to document the approved workflow-category boundaries for AegisOps n8n assets.

The approved workflow categories are alert ingest, enrich, approve, notify, and response.

## 2. Approved Workflow Categories

- `aegisops_alert_ingest` reserves the category for workflows that receive validated findings or alerts into the SOAR layer.
- `aegisops_enrich` reserves the category for read-oriented context gathering and triage support steps.
- `aegisops_approve` reserves the category for explicit approval handling before approval-required actions continue.
- `aegisops_notify` reserves the category for notification and operator-routing steps.
- `aegisops_response` reserves the category for controlled downstream execution after validation and required approvals are complete.

## 3. Placeholder Boundary

Placeholder directories and marker files under `n8n/workflows/` are not production workflows.

Do not infer live runtime behavior, integration coverage, or production-ready response logic from the current placeholders.

## 4. Control vs Execution Alignment

OpenSearch remains responsible for detection and analytics, while n8n is limited to approved orchestration, enrichment, approval handling, notification routing, and controlled downstream execution.

This separation preserves the approved control-versus-execution model and prevents raw detections from becoming unreviewed direct response actions.

## 5. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline.

Keep future workflow additions within the approved category boundary and preserve explicit approval gates for write or destructive actions.

## 6. Reference Documents

- `docs/architecture.md`
- `docs/requirements-baseline.md`
- `docs/repository-structure-baseline.md`
EOF
  git -C "${target}" add n8n/workflows/README.md
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
write_valid_doc "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing n8n workflow category guidance document"

missing_statement_repo="${workdir}/missing-statement"
create_repo "${missing_statement_repo}"
cat >"${missing_statement_repo}/n8n/workflows/README.md" <<'EOF'
# AegisOps n8n Workflow Category Guidance

This document explains the approved purpose and current boundaries of the tracked n8n workflow categories in AegisOps.

## 1. Purpose

This directory exists to document the approved workflow-category boundaries for AegisOps n8n assets.

The approved workflow categories are alert ingest, enrich, approve, notify, and response.

## 2. Approved Workflow Categories

- `aegisops_alert_ingest` reserves the category for workflows that receive validated findings or alerts into the SOAR layer.
- `aegisops_enrich` reserves the category for read-oriented context gathering and triage support steps.
- `aegisops_approve` reserves the category for explicit approval handling before approval-required actions continue.
- `aegisops_notify` reserves the category for notification and operator-routing steps.
- `aegisops_response` reserves the category for controlled downstream execution after validation and required approvals are complete.

## 3. Placeholder Boundary

Placeholder directories and marker files under `n8n/workflows/` are not production workflows.

## 4. Control vs Execution Alignment

OpenSearch remains responsible for detection and analytics, while n8n is limited to approved orchestration, enrichment, approval handling, notification routing, and controlled downstream execution.

## 5. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline.

## 6. Reference Documents

- `docs/architecture.md`
- `docs/requirements-baseline.md`
- `docs/repository-structure-baseline.md`
EOF
git -C "${missing_statement_repo}" add n8n/workflows/README.md
commit_fixture "${missing_statement_repo}"
assert_fails_with "${missing_statement_repo}" "Missing n8n workflow category guidance statement"

missing_reference_repo="${workdir}/missing-reference"
create_repo "${missing_reference_repo}"
cat >"${missing_reference_repo}/n8n/workflows/README.md" <<'EOF'
# AegisOps n8n Workflow Category Guidance

This document explains the approved purpose and current boundaries of the tracked n8n workflow categories in AegisOps.

## 1. Purpose

This directory exists to document the approved workflow-category boundaries for AegisOps n8n assets.

The approved workflow categories are alert ingest, enrich, approve, notify, and response.

## 2. Approved Workflow Categories

- `aegisops_alert_ingest` reserves the category for workflows that receive validated findings or alerts into the SOAR layer.
- `aegisops_enrich` reserves the category for read-oriented context gathering and triage support steps.
- `aegisops_approve` reserves the category for explicit approval handling before approval-required actions continue.
- `aegisops_notify` reserves the category for notification and operator-routing steps.
- `aegisops_response` reserves the category for controlled downstream execution after validation and required approvals are complete.

## 3. Placeholder Boundary

Placeholder directories and marker files under `n8n/workflows/` are not production workflows.

Do not infer live runtime behavior, integration coverage, or production-ready response logic from the current placeholders.

## 4. Control vs Execution Alignment

OpenSearch remains responsible for detection and analytics, while n8n is limited to approved orchestration, enrichment, approval handling, notification routing, and controlled downstream execution.

## 5. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline.

## 6. Reference Documents

- `docs/architecture.md`
- `docs/requirements-baseline.md`
EOF
git -C "${missing_reference_repo}" add n8n/workflows/README.md
commit_fixture "${missing_reference_repo}"
assert_fails_with "${missing_reference_repo}" "Missing n8n workflow category guidance reference"

echo "n8n workflow category guidance verifier tests passed."
