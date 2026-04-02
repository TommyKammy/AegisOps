#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/source-onboarding-contract.md"

required_headings=(
  "# AegisOps Source Onboarding Contract"
  "## 1. Purpose"
  "## 2. Contract Scope and Non-Goals"
  "## 3. Minimum Onboarding Package"
  "## 4. Detection-Ready Evidence Requirements"
  "## 5. Replay and Sample Data Expectations"
  "## 6. Readiness States"
  "## 7. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the minimum onboarding contract for any telemetry source family that seeks admission into the AegisOps normalized telemetry baseline."
  "It establishes the required evidence, ownership, field coverage, provenance, and readiness checks that must exist before downstream detection content can rely on a source family."
  "This contract governs documentation and validation expectations only. It does not approve live ingestion, parser deployment, source credentials, or runtime onboarding behavior."
  "Each source family onboarding package must identify the source family description, parser ownership, raw payload reference, normalization mapping, and sample data plan."
  '| Source family description | Required artifact |'
  '| Parser ownership and lifecycle | Required artifact |'
  '| Raw payload reference | Required artifact |'
  '| Normalization mapping | Required artifact |'
  '| Sample data and replay plan | Required artifact |'
  "Detection-ready status requires explicit evidence for canonical field coverage, timestamp quality, identity linkage, asset linkage, provenance, and parser version traceability."
  "Field coverage evidence must map source fields into the canonical telemetry schema baseline and must identify required, optional, unavailable, and intentionally deferred fields without ambiguity."
  '`Required` in this contract means the field group remains required by the canonical schema or family baseline even when a specific source family cannot currently supply it. Reviewers must not reinterpret required as optional merely because a source lacks the value.'
  '`Unavailable` means the source cannot credibly provide the field group for the reviewed scope without fabrication. `Intentionally deferred` means the source may support the field group later, but the mapping, parser, or evidence is not yet complete.'
  "Detection-ready review cannot treat a canonical required field group as satisfied by omission alone. A required field group may be unavailable or intentionally deferred only through an explicit documented exception path that states whether the gap blocks normalization, blocks detection readiness, or remains allowed for the current readiness state."
  'Timestamp evidence must identify the source event time, any collector-created time, ingest arrival time, known clock-quality limitations, and the chosen mapping for `@timestamp`, `event.created`, and `event.ingested`.'
  "Identity and asset linkage evidence must show which principals, hosts, workloads, tenants, devices, or observers the source can represent and where that context is absent or unreliable."
  "Provenance evidence must preserve source product, provider, module or dataset, collector path, and parser version details so normalized events remain traceable to their collection path."
  "A source family is not detection-ready until parser version evidence, field coverage evidence, and provenance evidence are documented and reviewable."
  "Required field groups from the canonical telemetry schema remain required even when a source family cannot yet satisfy them."
  "Shared required field groups that are unavailable block normalization unless the onboarding package documents an approved exception path."
  "Family required baseline coverage that is unavailable or intentionally deferred blocks detection-ready status unless the onboarding package documents an approved exception path and the resulting detector-use limits."
  "Replay-capable sample data must be sufficient for future parser and mapping validation without implying that live source onboarding is approved."
  "Sample datasets must preserve provenance, capture representative success and failure cases, and document any redaction or synthetic substitutions."
  "Sources that are not yet detection-ready must state their explicit non-goals, known schema gaps, and why downstream detections must not depend on them yet."
  'Readiness states must distinguish at least `candidate`, `schema-reviewed`, and `detection-ready` source families.'
  '`detection-ready` means the family has completed the required evidence package, has no unresolved intentionally deferred required coverage, and may be referenced by future detection content subject to separate detector and rollout review.'
  '`detection-ready` may rely on an explicit exception path only when the exception states which required coverage is missing, why the gap does not block the approved readiness scope, and which downstream detections remain prohibited.'
  "This contract is schema-driven and family-oriented. It must not become source-specific ad hoc guidance for individual products."
  'This contract remains aligned to `docs/canonical-telemetry-schema-baseline.md` and does not approve runtime parsers, ingest pipelines, or credential handling.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing source onboarding contract document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing source onboarding contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing source onboarding contract statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Source onboarding contract document is present and defines the required onboarding evidence, readiness states, and sample-data expectations."
