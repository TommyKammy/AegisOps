#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/canonical-telemetry-schema-baseline.md"

required_headings=(
  "# AegisOps Canonical Telemetry Schema Baseline"
  "## 1. Purpose"
  "## 2. Baseline Scope and Non-Goals"
  "## 3. Normalization Model and Field Classes"
  "## 4. Shared Normalized Field Groups"
  "## 5. Initial Log Family Baselines"
  "## 6. ECS Alignment and AegisOps Extensions"
  "## 7. Baseline Guardrails"
)

required_phrases=(
  'This document defines the canonical normalized telemetry schema baseline for the initial AegisOps log families.'
  'It establishes required, optional, and derived field expectations for future detection, correlation, enrichment, and case-oriented design work.'
  'This document defines schema semantics and preservation expectations only. It does not introduce live index mappings, ingestion pipelines, runtime transforms, or retention behavior.'
  'A `Raw Event` is the source record exactly as received or as losslessly wrapped by the ingest boundary before normalization.'
  'A `Normalized Event` is the analytics-plane record after the source event has been mapped into the approved AegisOps field contract.'
  '| Event classification | `event.*` | Required |'
  '| Time semantics | `@timestamp`, `event.created`, `event.ingested` | Required |'
  '| Source provenance | `observer.*`, `agent.*`, `event.provider`, `event.module`, `event.dataset`, `aegisops.provenance.*` | Required |'
  '| Identity references | `user.*`, `source.user.*`, `destination.user.*`, `related.user` | Optional |'
  '| Asset references | `host.*`, `observer.*`, `cloud.*`, `orchestrator.*`, `related.hosts` | Optional |'
  '| Network fields | `source.*`, `destination.*`, `network.*`, `url.*`, `dns.*`, `http.*`, `tls.*`, `related.ip` | Optional |'
  '| Process lineage | `process.*`, `process.parent.*`, `process.group_leader.*`, `related.process` | Optional |'
  '| AegisOps derived context | `rule.*`, `tags`, `related.*`, `aegisops.*` | Derived |'
  '### 5.1 Windows Security and Endpoint Telemetry'
  '### 5.2 Linux Operating System and Workload Telemetry'
  '### 5.3 Network Device and Network Security Telemetry'
  '### 5.4 SaaS Audit and Control-Plane Telemetry'
  'Normalized Windows telemetry must preserve actor identity, target identity when present, host identity, logon context, process lineage where available, and the original event channel or provider.'
  'Normalized Linux telemetry must preserve host identity, actor identity where present, process and parent process context where available, facility or collector provenance, and network endpoint context when the source record provides it.'
  'Normalized network telemetry must preserve observer identity, source and destination endpoint context, network transport and direction semantics, vendor or product provenance, and protocol-specific fields only when present in the original source.'
  'Normalized SaaS telemetry must preserve tenant or organization context, actor identity, target identity when present, API or control-plane action semantics, source IP or access path context when present, and the originating provider metadata.'
  'AegisOps adopts ECS as the baseline field naming and semantic contract for normalized events.'
  'AegisOps-specific fields are allowed only under the `aegisops.*` namespace.'
  'The baseline extension rule is additive: contributors may introduce `aegisops.*` fields when ECS lacks a stable home, but they must not redefine established ECS semantics or duplicate ECS fields with conflicting meaning.'
  'This baseline is schema-first and runtime-neutral. A future issue may define mappings, pipelines, transforms, or storage policies, but this document does not approve those runtime behaviors.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing canonical telemetry schema baseline document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing canonical telemetry schema heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing canonical telemetry schema statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Canonical telemetry schema baseline document is present and defines the required normalized field contracts and guardrails."
