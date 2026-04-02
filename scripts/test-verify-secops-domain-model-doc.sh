#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-secops-domain-model-doc.sh"

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

  printf '%s\n' "${doc_content}" >"${target}/docs/secops-domain-model.md"
  git -C "${target}" add docs/secops-domain-model.md
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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_doc "${valid_repo}" '# AegisOps SecOps Domain Model

## 1. Purpose

This document defines the first-class SecOps domain model for the AegisOps baseline.

This document defines baseline semantics, ownership boundaries, and state transitions only. It does not introduce runtime behavior, workflow automation, or architecture changes.

## 2. Core Domain Objects

| Object | Definition |
| ---- | ---- |
| `Raw Event` | Uninterpreted source telemetry before normalization. |
| `Normalized Event` | Event translated into the approved analytic schema. |
| `Detection Rule` | Reviewed detection logic that evaluates normalized telemetry. |
| `Finding` | Detection result produced when rule logic matches telemetry. |
| `Alert` | Routed analyst-facing item created from findings that require attention. |
| `Case` | Investigation record for an analyst work item. |
| `Incident` | Coordinated security event declaration across one or more cases. |
| `Asset` | Managed host, service, application, or environment entity relevant to operations. |
| `Identity` | Human or machine principal associated with activity or response scope. |
| `Evidence` | Preserved supporting record used to explain or justify SecOps decisions. |
| `Action Request` | Proposed response step waiting for approval or execution disposition. |
| `Approval Decision` | Explicit decision for a specific action request. |
| `Action Execution` | Record of the actual attempted or completed action. |
| `Disposition` | Closure or outcome classification applied to findings, alerts, cases, or incidents under the correct owner boundary. |

## 3. Relationship and State Boundaries

A finding is the normalized analytic assertion that detection logic matched relevant telemetry.

An alert is the routed operator-facing notification or queue item created from one or more findings after baseline triage policy decides analyst attention is required.

A case is the investigation record that groups alerts, evidence, analyst notes, and response coordination for one work item.

An incident is the higher-order security event declaration used when one or more cases represent a material security event that needs coordinated operational handling.

An approval decision records whether a specific action request is authorized, rejected, or expired.

An action execution records the actual downstream attempt or completion state for an approved or explicitly allowed action request.

OpenSearch findings, n8n workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states.

## 4. Baseline System of Record

| Object or boundary | Baseline system of record |
| ---- | ---- |
| `Finding` | OpenSearch detection and analytics plane |
| `Alert` | Future AegisOps alert routing and triage control layer |
| `Case` | Future AegisOps case management control layer |
| `Approval Decision` | Future AegisOps approval control layer |
| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state |

## 5. Baseline Alignment Notes

The baseline keeps detection, approval, and execution as separate control decisions.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing SecOps domain model document:"

missing_boundary_repo="${workdir}/missing-boundary"
create_repo "${missing_boundary_repo}"
write_doc "${missing_boundary_repo}" '# AegisOps SecOps Domain Model

## 1. Purpose

This document defines the first-class SecOps domain model for the AegisOps baseline.

This document defines baseline semantics, ownership boundaries, and state transitions only. It does not introduce runtime behavior, workflow automation, or architecture changes.

## 2. Core Domain Objects

| Object | Definition |
| ---- | ---- |
| `Raw Event` | Uninterpreted source telemetry before normalization. |
| `Normalized Event` | Event translated into the approved analytic schema. |
| `Detection Rule` | Reviewed detection logic that evaluates normalized telemetry. |
| `Finding` | Detection result produced when rule logic matches telemetry. |
| `Alert` | Routed analyst-facing item created from findings that require attention. |
| `Case` | Investigation record for an analyst work item. |
| `Incident` | Coordinated security event declaration across one or more cases. |
| `Asset` | Managed host, service, application, or environment entity relevant to operations. |
| `Identity` | Human or machine principal associated with activity or response scope. |
| `Evidence` | Preserved supporting record used to explain or justify SecOps decisions. |
| `Action Request` | Proposed response step waiting for approval or execution disposition. |
| `Approval Decision` | Explicit decision for a specific action request. |
| `Action Execution` | Record of the actual attempted or completed action. |
| `Disposition` | Closure or outcome classification applied to findings, alerts, cases, or incidents under the correct owner boundary. |

## 3. Relationship and State Boundaries

A finding is the normalized analytic assertion that detection logic matched relevant telemetry.

An alert is the routed operator-facing notification or queue item created from one or more findings after baseline triage policy decides analyst attention is required.

A case is the investigation record that groups alerts, evidence, analyst notes, and response coordination for one work item.

An incident is the higher-order security event declaration used when one or more cases represent a material security event that needs coordinated operational handling.

An approval decision records whether a specific action request is authorized, rejected, or expired.

An action execution records the actual downstream attempt or completion state for an approved or explicitly allowed action request.

## 4. Baseline System of Record

| Object or boundary | Baseline system of record |
| ---- | ---- |
| `Finding` | OpenSearch detection and analytics plane |
| `Alert` | Future AegisOps alert routing and triage control layer |
| `Case` | Future AegisOps case management control layer |
| `Approval Decision` | Future AegisOps approval control layer |
| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state |

## 5. Baseline Alignment Notes

The baseline keeps detection, approval, and execution as separate control decisions.'
commit_fixture "${missing_boundary_repo}"
assert_fails_with "${missing_boundary_repo}" "OpenSearch findings, n8n workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states."

echo "verify-secops-domain-model-doc tests passed"
