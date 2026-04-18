#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-25-multi-source-case-review-runbook.sh"

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

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/phase-25-multi-source-case-review-and-osquery-evidence-runbook.md"
  git -C "${target}" add docs/phase-25-multi-source-case-review-and-osquery-evidence-runbook.md
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
write_doc "${valid_repo}" '# Phase 25 Multi-Source Case Review and Osquery Evidence Runbook

## 1. Purpose

This runbook defines the reviewed operator procedure for Phase 25 business-hours operator casework.

It supplements `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md`, `docs/source-families/github-audit/analyst-triage-runbook.md`, `docs/source-families/entra-id/analyst-triage-runbook.md`, `docs/secops-business-hours-operating-model.md`, and `docs/wazuh-rule-lifecycle-runbook.md`.

The goal is to give operators one consistent procedure for multi-source case review, osquery-backed host evidence review, provenance interpretation, and ambiguity escalation without widening the reviewed authority model.

## 2. Scope and Non-Goals

This runbook does not authorize broad entity stitching, substrate-led investigation, external substrate authority promotion, direct GitHub or Entra ID actioning, or free-form host hunting outside the reviewed case chain.

osquery-backed host evidence may add host, process, or local-state context, but it must not become the authority for case identity, actor identity, approval truth, or lifecycle truth on its own.

## 3. Business-Hours Multi-Source Case Review Checklist

Operators should use the approved read-only inspection surfaces for this review:

- `python3 control-plane/main.py inspect-case-detail --case-id <case-id>`
- `python3 control-plane/main.py inspect-assistant-context --family case --record-id <case-id>`

## 4. Osquery-Backed Host Evidence Handling

osquery-backed host evidence is admissible only when the reviewed case already binds the host explicitly through `reviewed_context.asset.host_identifier`.

The approved osquery result kinds for this reviewed path are `host_state`, `process`, `local_user`, and `scheduled_query`.

The operator reviews osquery-backed host evidence as augmenting evidence:

## 5. Provenance and Ambiguity Interpretation

The reviewed ambiguity states for this runbook are:

Operators must not override an `unresolved` case detail state with a stronger assistant-facing interpretation unless a new authoritative reviewed link is recorded first.

## 6. Escalation and Out-of-Scope Boundaries

This runbook keeps broad entity stitching, substrate-led investigation, and external substrate authority explicitly out of scope for the reviewed Phase 25 path.

## 7. Repository-Local Verification Commands

The repository-local verification commands for this runbook are:

- `bash scripts/verify-phase-25-multi-source-case-review-runbook.sh`
- `python3 -m unittest control-plane.tests.test_phase25_multi_source_case_admission_docs`
- `python3 -m unittest control-plane.tests.test_phase25_osquery_host_context_validation`'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Phase 25 multi-source case review runbook:"

missing_commands_repo="${workdir}/missing-commands"
create_repo "${missing_commands_repo}"
write_doc "${missing_commands_repo}" '# Phase 25 Multi-Source Case Review and Osquery Evidence Runbook

## 1. Purpose

This runbook defines the reviewed operator procedure for Phase 25 business-hours operator casework.

It supplements `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md`, `docs/source-families/github-audit/analyst-triage-runbook.md`, `docs/source-families/entra-id/analyst-triage-runbook.md`, `docs/secops-business-hours-operating-model.md`, and `docs/wazuh-rule-lifecycle-runbook.md`.

The goal is to give operators one consistent procedure for multi-source case review, osquery-backed host evidence review, provenance interpretation, and ambiguity escalation without widening the reviewed authority model.

## 2. Scope and Non-Goals

This runbook does not authorize broad entity stitching, substrate-led investigation, external substrate authority promotion, direct GitHub or Entra ID actioning, or free-form host hunting outside the reviewed case chain.

osquery-backed host evidence may add host, process, or local-state context, but it must not become the authority for case identity, actor identity, approval truth, or lifecycle truth on its own.

## 3. Business-Hours Multi-Source Case Review Checklist

Operators should use the approved read-only inspection surfaces for this review:

- `python3 control-plane/main.py inspect-case-detail --case-id <case-id>`
- `python3 control-plane/main.py inspect-assistant-context --family case --record-id <case-id>`

## 4. Osquery-Backed Host Evidence Handling

osquery-backed host evidence is admissible only when the reviewed case already binds the host explicitly through `reviewed_context.asset.host_identifier`.

The approved osquery result kinds for this reviewed path are `host_state`, `process`, `local_user`, and `scheduled_query`.

The operator reviews osquery-backed host evidence as augmenting evidence:

## 5. Provenance and Ambiguity Interpretation

The reviewed ambiguity states for this runbook are:

Operators must not override an `unresolved` case detail state with a stronger assistant-facing interpretation unless a new authoritative reviewed link is recorded first.

## 6. Escalation and Out-of-Scope Boundaries

This runbook keeps broad entity stitching, substrate-led investigation, and external substrate authority explicitly out of scope for the reviewed Phase 25 path.

## 7. Repository-Local Verification Commands

The repository-local verification commands for this runbook are:'
commit_fixture "${missing_commands_repo}"
assert_fails_with "${missing_commands_repo}" 'Missing Phase 25 runbook statement: - `bash scripts/verify-phase-25-multi-source-case-review-runbook.sh`'

echo "verify-phase-25-multi-source-case-review-runbook tests passed"
