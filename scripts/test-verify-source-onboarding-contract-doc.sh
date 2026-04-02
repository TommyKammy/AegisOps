#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-source-onboarding-contract-doc.sh"

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

  printf '%s\n' "${doc_content}" >"${target}/docs/source-onboarding-contract.md"
  git -C "${target}" add docs/source-onboarding-contract.md
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
write_doc "${valid_repo}" '# AegisOps Source Onboarding Contract

## 1. Purpose

This document defines the minimum onboarding contract for any telemetry source family that seeks admission into the AegisOps normalized telemetry baseline.

It establishes the required evidence, ownership, field coverage, provenance, and readiness checks that must exist before downstream detection content can rely on a source family.

This contract governs documentation and validation expectations only. It does not approve live ingestion, parser deployment, source credentials, or runtime onboarding behavior.

## 2. Contract Scope and Non-Goals

Each source family onboarding package must identify the source family description, parser ownership, raw payload reference, normalization mapping, and sample data plan.

## 3. Minimum Onboarding Package

| Artifact | Expectation |
| ---- | ---- |
| Source family description | Required artifact |
| Parser ownership and lifecycle | Required artifact |
| Raw payload reference | Required artifact |
| Normalization mapping | Required artifact |
| Sample data and replay plan | Required artifact |

## 4. Detection-Ready Evidence Requirements

Detection-ready status requires explicit evidence for canonical field coverage, timestamp quality, identity linkage, asset linkage, provenance, and parser version traceability.

Field coverage evidence must map source fields into the canonical telemetry schema baseline and must identify required, optional, unavailable, and intentionally deferred fields without ambiguity.

`Required` in this contract means the field group remains required by the canonical schema or family baseline even when a specific source family cannot currently supply it. Reviewers must not reinterpret required as optional merely because a source lacks the value.

`Unavailable` means the source cannot credibly provide the field group for the reviewed scope without fabrication. `Intentionally deferred` means the source may support the field group later, but the mapping, parser, or evidence is not yet complete.

Detection-ready review cannot treat a canonical required field group as satisfied by omission alone. A required field group may be unavailable or intentionally deferred only through an explicit documented exception path that states whether the gap blocks normalization, blocks detection readiness, or remains allowed for the current readiness state.

Timestamp evidence must identify the source event time, any collector-created time, ingest arrival time, known clock-quality limitations, and the chosen mapping for `@timestamp`, `event.created`, and `event.ingested`.

Identity and asset linkage evidence must show which principals, hosts, workloads, tenants, devices, or observers the source can represent and where that context is absent or unreliable.

Provenance evidence must preserve source product, provider, module or dataset, collector path, and parser version details so normalized events remain traceable to their collection path.

A source family is not detection-ready until parser version evidence, field coverage evidence, and provenance evidence are documented and reviewable.

Required field groups from the canonical telemetry schema remain required even when a source family cannot yet satisfy them.

Shared required field groups that are unavailable block normalization unless the onboarding package documents an approved exception path.

Family required baseline coverage that is unavailable or intentionally deferred blocks detection-ready status unless the onboarding package documents an approved exception path and the resulting detector-use limits.

## 5. Replay and Sample Data Expectations

Replay-capable sample data must be sufficient for future parser and mapping validation without implying that live source onboarding is approved.

Sample datasets must preserve provenance, capture representative success and failure cases, and document any redaction or synthetic substitutions.

Sources that are not yet detection-ready must state their explicit non-goals, known schema gaps, and why downstream detections must not depend on them yet.

## 6. Readiness States

Readiness states must distinguish at least `candidate`, `schema-reviewed`, and `detection-ready` source families.

`detection-ready` means the family has completed the required evidence package, has no unresolved intentionally deferred required coverage, and may be referenced by future detection content subject to separate detector and rollout review.

`detection-ready` may rely on an explicit exception path only when the exception states which required coverage is missing, why the gap does not block the approved readiness scope, and which downstream detections remain prohibited.

This contract is schema-driven and family-oriented. It must not become source-specific ad hoc guidance for individual products.

## 7. Baseline Alignment Notes

This contract remains aligned to `docs/canonical-telemetry-schema-baseline.md` and does not approve runtime parsers, ingest pipelines, or credential handling.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing source onboarding contract document:"

missing_state_repo="${workdir}/missing-state"
create_repo "${missing_state_repo}"
write_doc "${missing_state_repo}" '# AegisOps Source Onboarding Contract

## 1. Purpose

This document defines the minimum onboarding contract for any telemetry source family that seeks admission into the AegisOps normalized telemetry baseline.

It establishes the required evidence, ownership, field coverage, provenance, and readiness checks that must exist before downstream detection content can rely on a source family.

This contract governs documentation and validation expectations only. It does not approve live ingestion, parser deployment, source credentials, or runtime onboarding behavior.

## 2. Contract Scope and Non-Goals

Each source family onboarding package must identify the source family description, parser ownership, raw payload reference, normalization mapping, and sample data plan.

## 3. Minimum Onboarding Package

| Artifact | Expectation |
| ---- | ---- |
| Source family description | Required artifact |
| Parser ownership and lifecycle | Required artifact |
| Raw payload reference | Required artifact |
| Normalization mapping | Required artifact |
| Sample data and replay plan | Required artifact |

## 4. Detection-Ready Evidence Requirements

Detection-ready status requires explicit evidence for canonical field coverage, timestamp quality, identity linkage, asset linkage, provenance, and parser version traceability.

Field coverage evidence must map source fields into the canonical telemetry schema baseline and must identify required, optional, unavailable, and intentionally deferred fields without ambiguity.

`Required` in this contract means the field group remains required by the canonical schema or family baseline even when a specific source family cannot currently supply it. Reviewers must not reinterpret required as optional merely because a source lacks the value.

`Unavailable` means the source cannot credibly provide the field group for the reviewed scope without fabrication. `Intentionally deferred` means the source may support the field group later, but the mapping, parser, or evidence is not yet complete.

Detection-ready review cannot treat a canonical required field group as satisfied by omission alone. A required field group may be unavailable or intentionally deferred only through an explicit documented exception path that states whether the gap blocks normalization, blocks detection readiness, or remains allowed for the current readiness state.

Timestamp evidence must identify the source event time, any collector-created time, ingest arrival time, known clock-quality limitations, and the chosen mapping for `@timestamp`, `event.created`, and `event.ingested`.

Identity and asset linkage evidence must show which principals, hosts, workloads, tenants, devices, or observers the source can represent and where that context is absent or unreliable.

Provenance evidence must preserve source product, provider, module or dataset, collector path, and parser version details so normalized events remain traceable to their collection path.

A source family is not detection-ready until parser version evidence, field coverage evidence, and provenance evidence are documented and reviewable.

Required field groups from the canonical telemetry schema remain required even when a source family cannot yet satisfy them.

Shared required field groups that are unavailable block normalization unless the onboarding package documents an approved exception path.

Family required baseline coverage that is unavailable or intentionally deferred blocks detection-ready status unless the onboarding package documents an approved exception path and the resulting detector-use limits.

## 5. Replay and Sample Data Expectations

Replay-capable sample data must be sufficient for future parser and mapping validation without implying that live source onboarding is approved.

Sample datasets must preserve provenance, capture representative success and failure cases, and document any redaction or synthetic substitutions.

Sources that are not yet detection-ready must state their explicit non-goals, known schema gaps, and why downstream detections must not depend on them yet.

## 6. Readiness States

`detection-ready` means the family has completed the required evidence package, has no unresolved intentionally deferred required coverage, and may be referenced by future detection content subject to separate detector and rollout review.

`detection-ready` may rely on an explicit exception path only when the exception states which required coverage is missing, why the gap does not block the approved readiness scope, and which downstream detections remain prohibited.

This contract is schema-driven and family-oriented. It must not become source-specific ad hoc guidance for individual products.
 
## 7. Baseline Alignment Notes

This contract remains aligned to `docs/canonical-telemetry-schema-baseline.md` and does not approve runtime parsers, ingest pipelines, or credential handling.'
commit_fixture "${missing_state_repo}"
assert_fails_with "${missing_state_repo}" 'Readiness states must distinguish at least `candidate`, `schema-reviewed`, and `detection-ready` source families.'

missing_required_semantics_repo="${workdir}/missing-required-semantics"
create_repo "${missing_required_semantics_repo}"
write_doc "${missing_required_semantics_repo}" '# AegisOps Source Onboarding Contract

## 1. Purpose

This document defines the minimum onboarding contract for any telemetry source family that seeks admission into the AegisOps normalized telemetry baseline.

It establishes the required evidence, ownership, field coverage, provenance, and readiness checks that must exist before downstream detection content can rely on a source family.

This contract governs documentation and validation expectations only. It does not approve live ingestion, parser deployment, source credentials, or runtime onboarding behavior.

## 2. Contract Scope and Non-Goals

Each source family onboarding package must identify the source family description, parser ownership, raw payload reference, normalization mapping, and sample data plan.

## 3. Minimum Onboarding Package

| Artifact | Expectation |
| ---- | ---- |
| Source family description | Required artifact |
| Parser ownership and lifecycle | Required artifact |
| Raw payload reference | Required artifact |
| Normalization mapping | Required artifact |
| Sample data and replay plan | Required artifact |

## 4. Detection-Ready Evidence Requirements

Detection-ready status requires explicit evidence for canonical field coverage, timestamp quality, identity linkage, asset linkage, provenance, and parser version traceability.

Field coverage evidence must map source fields into the canonical telemetry schema baseline and must identify required, optional, unavailable, and intentionally deferred fields without ambiguity.

Timestamp evidence must identify the source event time, any collector-created time, ingest arrival time, known clock-quality limitations, and the chosen mapping for `@timestamp`, `event.created`, and `event.ingested`.

Identity and asset linkage evidence must show which principals, hosts, workloads, tenants, devices, or observers the source can represent and where that context is absent or unreliable.

Provenance evidence must preserve source product, provider, module or dataset, collector path, and parser version details so normalized events remain traceable to their collection path.

A source family is not detection-ready until parser version evidence, field coverage evidence, and provenance evidence are documented and reviewable.

## 5. Replay and Sample Data Expectations

Replay-capable sample data must be sufficient for future parser and mapping validation without implying that live source onboarding is approved.

Sample datasets must preserve provenance, capture representative success and failure cases, and document any redaction or synthetic substitutions.

Sources that are not yet detection-ready must state their explicit non-goals, known schema gaps, and why downstream detections must not depend on them yet.

## 6. Readiness States

Readiness states must distinguish at least `candidate`, `schema-reviewed`, and `detection-ready` source families.

This contract is schema-driven and family-oriented. It must not become source-specific ad hoc guidance for individual products.

## 7. Baseline Alignment Notes

This contract remains aligned to `docs/canonical-telemetry-schema-baseline.md` and does not approve runtime parsers, ingest pipelines, or credential handling.'
commit_fixture "${missing_required_semantics_repo}"
assert_fails_with "${missing_required_semantics_repo}" '`Required` in this contract means the field group remains required by the canonical schema or family baseline even when a specific source family cannot currently supply it. Reviewers must not reinterpret required as optional merely because a source lacks the value.'

echo "verify-source-onboarding-contract-doc tests passed"
