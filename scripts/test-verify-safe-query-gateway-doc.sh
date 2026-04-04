#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-safe-query-gateway-doc.sh"

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

  printf '%s\n' "${doc_content}" >"${target}/docs/safe-query-gateway-and-tool-policy.md"
  git -C "${target}" add docs/safe-query-gateway-and-tool-policy.md
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
write_doc "${valid_repo}" '# AegisOps Safe Query Gateway and AI Hunt Tool Policy

## 1. Purpose

This document defines the baseline Safe Query Gateway and tool policy for future AI-assisted hunt workflows.

This document defines request, validation, and trust-boundary policy only. It does not authorize direct AI access to OpenSearch, unrestricted public web access, or execution-capable tools.

## 2. Safe Query Gateway Boundary

AI-authored free-form queries must never be executed directly against OpenSearch, SQL engines, shell surfaces, or public-internet search tools.

## 3. Structured Query Intent Contract

Every hunt request must be expressed as structured query intent rather than raw query text.

## 4. Validation and Deterministic Query Generation

The gateway must compile validated intent into deterministic query templates owned by AegisOps rather than passing model-authored syntax through to a backend.

Validation must reject requests that exceed allowlisted index scope, approved field access, bounded time range, row cap, aggregation policy, or query cost budget.

## 5. Allowlists and Budget Limits

| Control | Policy |
| ---- | ---- |
| `Index scope` | Only explicitly allowlisted indices or data views for the approved hunt family may be queried. |
| `Time range` | Every request must carry a bounded start and end time, and the policy must enforce a fixed time cap. |
| `Field access` | Requested filters, projections, sort keys, and grouping fields must come from an allowlist tied to the hunt family. |
| `Row cap` | The gateway must enforce a maximum result window and refuse unbounded result retrieval. |
| `Aggregation` | Aggregations are denied by default and may be enabled only for approved templates with bounded cardinality. |
| `Cost budget` | Each request must stay within a deterministic query-cost budget before execution is attempted. |

## 6. Citation-Bearing Response Contract

Returned observations must carry citations that let an analyst trace each statement back to the underlying index, document identifier or bucket key, and query window used to produce it.

A response without sufficient citations must be treated as advisory text only and must not be promoted to evidence, case facts, or approval context.

## 7. Tool Policy Trust Classes

| Trust class | Allowed source family | Boundary expectation |
| ---- | ---- | ---- |
| `Internal-only read` | Approved internal AegisOps data sources such as OpenSearch findings, normalized event stores, or internal case metadata. | No public-internet access and no provider egress beyond the approved internal boundary. |
| `Approved-partner read` | Bounded reads to named external services under contract or delegated trust, such as ticketing, threat intel, or CMDB APIs. | Egress is allowed only to explicitly approved partners with scoped fields, request logging, and ownership. |
| `Public-internet read` | Searches or retrieval against public web content outside approved partner boundaries. | Disabled by default for hunt workflows and must be modeled as a separate trust boundary with explicit approval if ever enabled later. |

## 8. Failure Handling

Validation failure must return a machine-readable rejection reason that identifies which policy boundary was crossed without silently widening the request.

Timeouts, partial backend failures, missing citations, or over-budget results must fail closed rather than returning uncited speculative summaries.

## 9. Baseline Alignment Notes

This policy preserves the baseline separation between analytics, advisory AI assistance, approval state, and execution surfaces while making data egress risk explicit by trust class.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing safe query gateway document:"

missing_budget_repo="${workdir}/missing-budget"
create_repo "${missing_budget_repo}"
write_doc "${missing_budget_repo}" '# AegisOps Safe Query Gateway and AI Hunt Tool Policy

## 1. Purpose

This document defines the baseline Safe Query Gateway and tool policy for future AI-assisted hunt workflows.

This document defines request, validation, and trust-boundary policy only. It does not authorize direct AI access to OpenSearch, unrestricted public web access, or execution-capable tools.

## 2. Safe Query Gateway Boundary

AI-authored free-form queries must never be executed directly against OpenSearch, SQL engines, shell surfaces, or public-internet search tools.

## 3. Structured Query Intent Contract

Every hunt request must be expressed as structured query intent rather than raw query text.

## 4. Validation and Deterministic Query Generation

The gateway must compile validated intent into deterministic query templates owned by AegisOps rather than passing model-authored syntax through to a backend.

Validation must reject requests that exceed allowlisted index scope, approved field access, bounded time range, row cap, aggregation policy, or query cost budget.

## 5. Allowlists and Budget Limits

| Control | Policy |
| ---- | ---- |
| `Index scope` | Only explicitly allowlisted indices or data views for the approved hunt family may be queried. |
| `Time range` | Every request must carry a bounded start and end time, and the policy must enforce a fixed time cap. |
| `Field access` | Requested filters, projections, sort keys, and grouping fields must come from an allowlist tied to the hunt family. |
| `Row cap` | The gateway must enforce a maximum result window and refuse unbounded result retrieval. |
| `Aggregation` | Aggregations are denied by default and may be enabled only for approved templates with bounded cardinality. |

## 6. Citation-Bearing Response Contract

Returned observations must carry citations that let an analyst trace each statement back to the underlying index, document identifier or bucket key, and query window used to produce it.

A response without sufficient citations must be treated as advisory text only and must not be promoted to evidence, case facts, or approval context.

## 7. Tool Policy Trust Classes

| Trust class | Allowed source family | Boundary expectation |
| ---- | ---- | ---- |
| `Internal-only read` | Approved internal AegisOps data sources such as OpenSearch findings, normalized event stores, or internal case metadata. | No public-internet access and no provider egress beyond the approved internal boundary. |
| `Approved-partner read` | Bounded reads to named external services under contract or delegated trust, such as ticketing, threat intel, or CMDB APIs. | Egress is allowed only to explicitly approved partners with scoped fields, request logging, and ownership. |
| `Public-internet read` | Searches or retrieval against public web content outside approved partner boundaries. | Disabled by default for hunt workflows and must be modeled as a separate trust boundary with explicit approval if ever enabled later. |

## 8. Failure Handling

Validation failure must return a machine-readable rejection reason that identifies which policy boundary was crossed without silently widening the request.

Timeouts, partial backend failures, missing citations, or over-budget results must fail closed rather than returning uncited speculative summaries.

## 9. Baseline Alignment Notes

This policy preserves the baseline separation between analytics, advisory AI assistance, approval state, and execution surfaces while making data egress risk explicit by trust class.'
commit_fixture "${missing_budget_repo}"
assert_fails_with "${missing_budget_repo}" '| `Cost budget` | Each request must stay within a deterministic query-cost budget before execution is attempted. |'

missing_trust_class_repo="${workdir}/missing-trust-class"
create_repo "${missing_trust_class_repo}"
write_doc "${missing_trust_class_repo}" '# AegisOps Safe Query Gateway and AI Hunt Tool Policy

## 1. Purpose

This document defines the baseline Safe Query Gateway and tool policy for future AI-assisted hunt workflows.

This document defines request, validation, and trust-boundary policy only. It does not authorize direct AI access to OpenSearch, unrestricted public web access, or execution-capable tools.

## 2. Safe Query Gateway Boundary

AI-authored free-form queries must never be executed directly against OpenSearch, SQL engines, shell surfaces, or public-internet search tools.

## 3. Structured Query Intent Contract

Every hunt request must be expressed as structured query intent rather than raw query text.

## 4. Validation and Deterministic Query Generation

The gateway must compile validated intent into deterministic query templates owned by AegisOps rather than passing model-authored syntax through to a backend.

Validation must reject requests that exceed allowlisted index scope, approved field access, bounded time range, row cap, aggregation policy, or query cost budget.

## 5. Allowlists and Budget Limits

| Control | Policy |
| ---- | ---- |
| `Index scope` | Only explicitly allowlisted indices or data views for the approved hunt family may be queried. |
| `Time range` | Every request must carry a bounded start and end time, and the policy must enforce a fixed time cap. |
| `Field access` | Requested filters, projections, sort keys, and grouping fields must come from an allowlist tied to the hunt family. |
| `Row cap` | The gateway must enforce a maximum result window and refuse unbounded result retrieval. |
| `Aggregation` | Aggregations are denied by default and may be enabled only for approved templates with bounded cardinality. |
| `Cost budget` | Each request must stay within a deterministic query-cost budget before execution is attempted. |

## 6. Citation-Bearing Response Contract

Returned observations must carry citations that let an analyst trace each statement back to the underlying index, document identifier or bucket key, and query window used to produce it.

A response without sufficient citations must be treated as advisory text only and must not be promoted to evidence, case facts, or approval context.

## 7. Tool Policy Trust Classes

| Trust class | Allowed source family | Boundary expectation |
| ---- | ---- | ---- |
| `Internal-only read` | Approved internal AegisOps data sources such as OpenSearch findings, normalized event stores, or internal case metadata. | No public-internet access and no provider egress beyond the approved internal boundary. |
| `Approved-partner read` | Bounded reads to named external services under contract or delegated trust, such as ticketing, threat intel, or CMDB APIs. | Egress is allowed only to explicitly approved partners with scoped fields, request logging, and ownership. |

## 8. Failure Handling

Validation failure must return a machine-readable rejection reason that identifies which policy boundary was crossed without silently widening the request.

Timeouts, partial backend failures, missing citations, or over-budget results must fail closed rather than returning uncited speculative summaries.

## 9. Baseline Alignment Notes

This policy preserves the baseline separation between analytics, advisory AI assistance, approval state, and execution surfaces while making data egress risk explicit by trust class.'
commit_fixture "${missing_trust_class_repo}"
assert_fails_with "${missing_trust_class_repo}" '| `Public-internet read` | Searches or retrieval against public web content outside approved partner boundaries. | Disabled by default for hunt workflows and must be modeled as a separate trust boundary with explicit approval if ever enabled later. |'
