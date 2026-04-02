#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-canonical-telemetry-schema-doc.sh"

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

  printf '%s\n' "${doc_content}" >"${target}/docs/canonical-telemetry-schema-baseline.md"
  git -C "${target}" add docs/canonical-telemetry-schema-baseline.md
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
write_doc "${valid_repo}" '# AegisOps Canonical Telemetry Schema Baseline

## 1. Purpose

This document defines the canonical normalized telemetry schema baseline for the initial AegisOps log families.

It establishes required, optional, and derived field expectations for future detection, correlation, enrichment, and case-oriented design work.

This document defines schema semantics and preservation expectations only. It does not introduce live index mappings, ingestion pipelines, runtime transforms, or retention behavior.

## 2. Baseline Scope and Non-Goals

A `Raw Event` is the source record exactly as received or as losslessly wrapped by the ingest boundary before normalization.

A `Normalized Event` is the analytics-plane record after the source event has been mapped into the approved AegisOps field contract.

Required means normalization-required, not universally source-populated. When a source family cannot supply a required field group for some records, the gap must be documented as an explicit exception path rather than silently reclassifying the group as optional.

## 3. Normalization Model and Field Classes

Baseline classes are required, optional, and derived.

Onboarding evidence may additionally mark a field group as unavailable or intentionally deferred for a source family review, but those are review states rather than field classes. They do not change a canonical required field group into an optional one.

- `Unavailable` means the source cannot credibly provide the field group without fabrication for the reviewed scope. For shared required groups, that normally blocks normalization unless an explicit exception path is approved. For family baseline coverage, it normally blocks detection-ready status unless an explicit exception path says otherwise.
- `Intentionally deferred` means the source family may support the field group later but the mapping, evidence, or parser work is not yet complete. Deferred required coverage blocks detection-ready status until the deferred gap is resolved or an explicit exception path is approved.

## 4. Shared Normalized Field Groups

| Field group | Representative fields | Class |
| ---- | ---- | ---- |
| Event classification | `event.*` | Required |
| Time semantics | `@timestamp`, `event.created`, `event.ingested` | Required |
| Source provenance | `observer.*`, `agent.*`, `event.provider`, `event.module`, `event.dataset`, `aegisops.provenance.*` | Required |
| Identity references | `user.*`, `source.user.*`, `destination.user.*`, `related.user` | Optional |
| Asset references | `host.*`, `observer.*`, `cloud.*`, `orchestrator.*`, `related.hosts` | Optional |
| Network fields | `source.*`, `destination.*`, `network.*`, `url.*`, `dns.*`, `http.*`, `tls.*`, `related.ip` | Optional |
| Process lineage | `process.*`, `process.parent.*`, `process.group_leader.*`, `related.process` | Optional |
| AegisOps derived context | `rule.*`, `tags`, `related.*`, `aegisops.*` | Derived |

## 5. Initial Log Family Baselines

- Shared field groups marked `Required` in Section 4 are event-level normalization requirements.
- Family sections marked "Required baseline coverage" are source-family readiness requirements for the listed semantic areas. They do not mean every representative field appears on every event; they mean the family must preserve that semantic area when the source exposes it and must document any approved exception path when it cannot.
- A missing family baseline requirement must be classified during onboarding as either a normalization blocker, a detection-ready blocker, or an explicit exception path with allowed downstream usage.

### 5.1 Windows Security and Endpoint Telemetry

Normalized Windows telemetry must preserve actor identity, target identity when present, host identity, logon context, process lineage where available, and the original event channel or provider.

### 5.2 Linux Operating System and Workload Telemetry

Normalized Linux telemetry must preserve host identity, actor identity where present, process and parent process context where available, facility or collector provenance, and network endpoint context when the source record provides it.

### 5.3 Network Device and Network Security Telemetry

Normalized network telemetry must preserve observer identity, source and destination endpoint context, network transport and direction semantics, vendor or product provenance, and protocol-specific fields only when present in the original source.

### 5.4 SaaS Audit and Control-Plane Telemetry

Normalized SaaS telemetry must preserve tenant or organization context, actor identity, target identity when present, API or control-plane action semantics, source IP or access path context when present, and the originating provider metadata.

## 6. ECS Alignment and AegisOps Extensions

AegisOps adopts ECS as the baseline field naming and semantic contract for normalized events.

AegisOps-specific fields are allowed only under the `aegisops.*` namespace.

The baseline extension rule is additive: contributors may introduce `aegisops.*` fields when ECS lacks a stable home, but they must not redefine established ECS semantics or duplicate ECS fields with conflicting meaning.

## 7. Baseline Guardrails

This baseline is schema-first and runtime-neutral. A future issue may define mappings, pipelines, transforms, or storage policies, but this document does not approve those runtime behaviors.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing canonical telemetry schema baseline document:"

missing_family_repo="${workdir}/missing-family"
create_repo "${missing_family_repo}"
write_doc "${missing_family_repo}" '# AegisOps Canonical Telemetry Schema Baseline

## 1. Purpose

This document defines the canonical normalized telemetry schema baseline for the initial AegisOps log families.

It establishes required, optional, and derived field expectations for future detection, correlation, enrichment, and case-oriented design work.

This document defines schema semantics and preservation expectations only. It does not introduce live index mappings, ingestion pipelines, runtime transforms, or retention behavior.

## 2. Baseline Scope and Non-Goals

A `Raw Event` is the source record exactly as received or as losslessly wrapped by the ingest boundary before normalization.

A `Normalized Event` is the analytics-plane record after the source event has been mapped into the approved AegisOps field contract.

Required means normalization-required, not universally source-populated. When a source family cannot supply a required field group for some records, the gap must be documented as an explicit exception path rather than silently reclassifying the group as optional.

## 3. Normalization Model and Field Classes

Baseline classes are required, optional, and derived.

Onboarding evidence may additionally mark a field group as unavailable or intentionally deferred for a source family review, but those are review states rather than field classes. They do not change a canonical required field group into an optional one.

- `Unavailable` means the source cannot credibly provide the field group without fabrication for the reviewed scope. For shared required groups, that normally blocks normalization unless an explicit exception path is approved. For family baseline coverage, it normally blocks detection-ready status unless an explicit exception path says otherwise.
- `Intentionally deferred` means the source family may support the field group later but the mapping, evidence, or parser work is not yet complete. Deferred required coverage blocks detection-ready status until the deferred gap is resolved or an explicit exception path is approved.

## 4. Shared Normalized Field Groups

| Field group | Representative fields | Class |
| ---- | ---- | ---- |
| Event classification | `event.*` | Required |
| Time semantics | `@timestamp`, `event.created`, `event.ingested` | Required |
| Source provenance | `observer.*`, `agent.*`, `event.provider`, `event.module`, `event.dataset`, `aegisops.provenance.*` | Required |
| Identity references | `user.*`, `source.user.*`, `destination.user.*`, `related.user` | Optional |
| Asset references | `host.*`, `observer.*`, `cloud.*`, `orchestrator.*`, `related.hosts` | Optional |
| Network fields | `source.*`, `destination.*`, `network.*`, `url.*`, `dns.*`, `http.*`, `tls.*`, `related.ip` | Optional |
| Process lineage | `process.*`, `process.parent.*`, `process.group_leader.*`, `related.process` | Optional |
| AegisOps derived context | `rule.*`, `tags`, `related.*`, `aegisops.*` | Derived |

## 5. Initial Log Family Baselines

- Shared field groups marked `Required` in Section 4 are event-level normalization requirements.
- Family sections marked "Required baseline coverage" are source-family readiness requirements for the listed semantic areas. They do not mean every representative field appears on every event; they mean the family must preserve that semantic area when the source exposes it and must document any approved exception path when it cannot.
- A missing family baseline requirement must be classified during onboarding as either a normalization blocker, a detection-ready blocker, or an explicit exception path with allowed downstream usage.

### 5.1 Windows Security and Endpoint Telemetry

Normalized Windows telemetry must preserve actor identity, target identity when present, host identity, logon context, process lineage where available, and the original event channel or provider.

## 6. ECS Alignment and AegisOps Extensions

AegisOps adopts ECS as the baseline field naming and semantic contract for normalized events.

AegisOps-specific fields are allowed only under the `aegisops.*` namespace.

The baseline extension rule is additive: contributors may introduce `aegisops.*` fields when ECS lacks a stable home, but they must not redefine established ECS semantics or duplicate ECS fields with conflicting meaning.

## 7. Baseline Guardrails

This baseline is schema-first and runtime-neutral. A future issue may define mappings, pipelines, transforms, or storage policies, but this document does not approve those runtime behaviors.'
commit_fixture "${missing_family_repo}"
assert_fails_with "${missing_family_repo}" "### 5.2 Linux Operating System and Workload Telemetry"

missing_required_semantics_repo="${workdir}/missing-required-semantics"
create_repo "${missing_required_semantics_repo}"
write_doc "${missing_required_semantics_repo}" '# AegisOps Canonical Telemetry Schema Baseline

## 1. Purpose

This document defines the canonical normalized telemetry schema baseline for the initial AegisOps log families.

It establishes required, optional, and derived field expectations for future detection, correlation, enrichment, and case-oriented design work.

This document defines schema semantics and preservation expectations only. It does not introduce live index mappings, ingestion pipelines, runtime transforms, or retention behavior.

## 2. Baseline Scope and Non-Goals

A `Raw Event` is the source record exactly as received or as losslessly wrapped by the ingest boundary before normalization.

A `Normalized Event` is the analytics-plane record after the source event has been mapped into the approved AegisOps field contract.

## 3. Normalization Model and Field Classes

Baseline classes are required, optional, and derived.

## 4. Shared Normalized Field Groups

| Field group | Representative fields | Class |
| ---- | ---- | ---- |
| Event classification | `event.*` | Required |
| Time semantics | `@timestamp`, `event.created`, `event.ingested` | Required |
| Source provenance | `observer.*`, `agent.*`, `event.provider`, `event.module`, `event.dataset`, `aegisops.provenance.*` | Required |
| Identity references | `user.*`, `source.user.*`, `destination.user.*`, `related.user` | Optional |
| Asset references | `host.*`, `observer.*`, `cloud.*`, `orchestrator.*`, `related.hosts` | Optional |
| Network fields | `source.*`, `destination.*`, `network.*`, `url.*`, `dns.*`, `http.*`, `tls.*`, `related.ip` | Optional |
| Process lineage | `process.*`, `process.parent.*`, `process.group_leader.*`, `related.process` | Optional |
| AegisOps derived context | `rule.*`, `tags`, `related.*`, `aegisops.*` | Derived |

## 5. Initial Log Family Baselines

### 5.1 Windows Security and Endpoint Telemetry

Normalized Windows telemetry must preserve actor identity, target identity when present, host identity, logon context, process lineage where available, and the original event channel or provider.

### 5.2 Linux Operating System and Workload Telemetry

Normalized Linux telemetry must preserve host identity, actor identity where present, process and parent process context where available, facility or collector provenance, and network endpoint context when the source record provides it.

### 5.3 Network Device and Network Security Telemetry

Normalized network telemetry must preserve observer identity, source and destination endpoint context, network transport and direction semantics, vendor or product provenance, and protocol-specific fields only when present in the original source.

### 5.4 SaaS Audit and Control-Plane Telemetry

Normalized SaaS telemetry must preserve tenant or organization context, actor identity, target identity when present, API or control-plane action semantics, source IP or access path context when present, and the originating provider metadata.

## 6. ECS Alignment and AegisOps Extensions

AegisOps adopts ECS as the baseline field naming and semantic contract for normalized events.

AegisOps-specific fields are allowed only under the `aegisops.*` namespace.

The baseline extension rule is additive: contributors may introduce `aegisops.*` fields when ECS lacks a stable home, but they must not redefine established ECS semantics or duplicate ECS fields with conflicting meaning.

## 7. Baseline Guardrails

This baseline is schema-first and runtime-neutral. A future issue may define mappings, pipelines, transforms, or storage policies, but this document does not approve those runtime behaviors.'
commit_fixture "${missing_required_semantics_repo}"
assert_fails_with "${missing_required_semantics_repo}" "Required means normalization-required, not universally source-populated."

echo "verify-canonical-telemetry-schema-doc tests passed"
