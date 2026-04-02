# AegisOps Canonical Telemetry Schema Baseline

## 1. Purpose

This document defines the canonical normalized telemetry schema baseline for the initial AegisOps log families.

It establishes required, optional, and derived field expectations for future detection, correlation, enrichment, and case-oriented design work.

This document defines schema semantics and preservation expectations only. It does not introduce live index mappings, ingestion pipelines, runtime transforms, or retention behavior.

## 2. Baseline Scope and Non-Goals

The initial approved log families for this baseline are the same families reserved by the current OpenSearch placeholder assets and naming baseline:

- Windows security and endpoint telemetry
- Linux operating system and workload telemetry
- Network device and network security telemetry
- SaaS audit and control-plane telemetry

A `Raw Event` is the source record exactly as received or as losslessly wrapped by the ingest boundary before normalization.

A `Normalized Event` is the analytics-plane record after the source event has been mapped into the approved AegisOps field contract.

The normalized contract exists so downstream detections, findings, correlation logic, enrichment, and case-oriented control-plane design can rely on stable field semantics even when source products differ.

This baseline does not require every source to populate every field. It requires each source family to preserve the highest-fidelity values it has for the approved field groups and to avoid silent semantic drift during normalization.

## 3. Normalization Model and Field Classes

Normalized fields are grouped into three classes:

- Required fields must exist on every normalized event in the initial approved families unless the source record is unusable.
- Optional fields should be populated when the source or collector provides the necessary value without fabrication.
- Derived fields may be added by AegisOps logic only when their origin remains explainable and the source-derived values remain distinguishable from derived context.

Raw source payload preservation rules:

- Source-specific raw payloads must remain distinguishable from normalized fields.
- Raw payload retention or storage location is a runtime concern and is intentionally out of scope here.
- When future implementations retain the original payload or source-native identifiers, provenance fields must make that preservation path explicit.

## 4. Shared Normalized Field Groups

| Field group | Representative fields | Class | Baseline expectation |
| ---- | ---- | ---- | ---- |
| Event classification | `event.*` | Required | Every normalized event must classify the activity with stable event kind, category, type, and action semantics appropriate to the source. |
| Time semantics | `@timestamp`, `event.created`, `event.ingested` | Required | Each normalized event must preserve the source event time when known, the collector or normalization creation time when known, and the ingest arrival time when known. |
| Source provenance | `observer.*`, `agent.*`, `event.provider`, `event.module`, `event.dataset`, `aegisops.provenance.*` | Required | The normalized event must preserve which product, collector, provider, integration, or module produced the record and which AegisOps ingest path handled it. |
| Identity references | `user.*`, `source.user.*`, `destination.user.*`, `related.user` | Optional | Identity fields should preserve the acting principal, target principal, and any related usernames or IDs without collapsing distinct roles into one field. |
| Asset references | `host.*`, `observer.*`, `cloud.*`, `orchestrator.*`, `related.hosts` | Optional | Asset fields should preserve the affected host, workload, control-plane tenant, observer, or service boundary when the source exposes them. |
| Network fields | `source.*`, `destination.*`, `network.*`, `url.*`, `dns.*`, `http.*`, `tls.*`, `related.ip` | Optional | Network context should preserve endpoint identity, ports, transport, protocol, direction, URLs, DNS names, and related IPs only when the source provides them. |
| Process lineage | `process.*`, `process.parent.*`, `process.group_leader.*`, `related.process` | Optional | Process-capable telemetry should preserve executable, command-line, parent-child linkage, and stable process identifiers where the source supports them. |
| AegisOps derived context | `rule.*`, `tags`, `related.*`, `aegisops.*` | Derived | Derived enrichment must stay additive, explainable, and separate from the raw source meaning. |

### 4.1 Timestamp Semantics

- `@timestamp` is the canonical event occurrence time used for analytics and correlation. It should map to the best source-recorded occurrence time available.
- `event.created` records when the event record was first created by the source product or collector, when that distinction is available separately from occurrence time.
- `event.ingested` records when the AegisOps analytics plane accepted the event.
- When clock quality or source time uncertainty is material, provenance notes under `aegisops.provenance.*` should preserve the limitation rather than silently rewriting the meaning of `@timestamp`.

### 4.2 Identity and Asset Reference Rules

- `user.*` should identify the primary actor represented by the event.
- `source.user.*` and `destination.user.*` should be used only when the source distinguishes origin and target principals.
- `host.*` should identify the host or workload where the activity occurred, while `observer.*` should identify the appliance, sensor, or service that observed or emitted the record.
- `related.user`, `related.hosts`, and similar correlation helpers may aggregate references but must not replace the more specific first-class fields.

### 4.3 Source Provenance Rules

- Normalization must preserve the source product, source provider, source dataset or module, and collector path without erasing vendor-specific identity.
- `aegisops.provenance.*` is reserved for AegisOps-specific provenance details such as ingest path identifiers, parser version references, or normalization notes when ECS does not provide a stable equivalent.
- Provenance fields must make it possible to trace a normalized event back to its source family, product, and collection path.

### 4.4 Process and Network Semantics

- Process lineage is expected only for telemetry families that can credibly supply it; absence must not be fabricated.
- Network direction and transport semantics must follow the source meaning and must not infer bidirectional session claims from one-sided records.
- Source and destination fields must preserve endpoint roles as reported by the source, especially for firewall, proxy, VPN, and SaaS access logs where observer perspective can differ from host-local semantics.

## 5. Initial Log Family Baselines

### 5.1 Windows Security and Endpoint Telemetry

Required baseline coverage for Windows telemetry:

- Event classification and timestamp semantics
- Source provenance including event channel, provider, and collector or agent identity
- Host identity and asset references
- Actor identity and target identity when present

Optional baseline coverage for Windows telemetry:

- Logon session context, token or integrity details, and group references
- Process lineage and command-line context
- Source and destination network context for remote access or lateral movement records

Derived baseline coverage for Windows telemetry:

- Related user, host, IP, and process correlation fields
- AegisOps-specific provenance annotations under `aegisops.*`

Normalized Windows telemetry must preserve actor identity, target identity when present, host identity, logon context, process lineage where available, and the original event channel or provider.

### 5.2 Linux Operating System and Workload Telemetry

Required baseline coverage for Linux telemetry:

- Event classification and timestamp semantics
- Source provenance including collector identity, module, facility, or subsystem where present
- Host identity and workload context when available

Optional baseline coverage for Linux telemetry:

- Actor identity such as user, account, or service principal
- Process and parent process details
- File, command, and network endpoint context when present in the source record

Derived baseline coverage for Linux telemetry:

- Related host, user, IP, and process correlation helpers
- AegisOps provenance annotations under `aegisops.*`

Normalized Linux telemetry must preserve host identity, actor identity where present, process and parent process context where available, facility or collector provenance, and network endpoint context when the source record provides it.

### 5.3 Network Device and Network Security Telemetry

Required baseline coverage for network telemetry:

- Event classification and timestamp semantics
- Observer identity for the device, sensor, or service that emitted the record
- Source and destination endpoint context to the fidelity the source provides
- Transport, protocol, and vendor or product provenance

Optional baseline coverage for network telemetry:

- URL, DNS, HTTP, TLS, NAT, interface, and directionality details
- User identity or asset ownership context when the network source provides it

Derived baseline coverage for network telemetry:

- Correlation-friendly `related.ip`, `related.hosts`, and tagging fields
- AegisOps provenance annotations under `aegisops.*`

Normalized network telemetry must preserve observer identity, source and destination endpoint context, network transport and direction semantics, vendor or product provenance, and protocol-specific fields only when present in the original source.

### 5.4 SaaS Audit and Control-Plane Telemetry

Required baseline coverage for SaaS telemetry:

- Event classification and timestamp semantics
- Provider, tenant, organization, or workspace provenance
- Actor identity and action semantics

Optional baseline coverage for SaaS telemetry:

- Target identity or object references
- Source IP, user agent, session, device, API client, or access-path context when the provider supplies them
- Cloud account or organizational scoping fields where relevant

Derived baseline coverage for SaaS telemetry:

- Correlation helpers and tags
- AegisOps provenance annotations under `aegisops.*`

Normalized SaaS telemetry must preserve tenant or organization context, actor identity, target identity when present, API or control-plane action semantics, source IP or access path context when present, and the originating provider metadata.

## 6. ECS Alignment and AegisOps Extensions

AegisOps adopts ECS as the baseline field naming and semantic contract for normalized events.

ECS-aligned fields should be used whenever ECS already provides a stable semantic home for the source value.

AegisOps-specific fields are allowed only under the `aegisops.*` namespace.

The baseline extension rule is additive: contributors may introduce `aegisops.*` fields when ECS lacks a stable home, but they must not redefine established ECS semantics or duplicate ECS fields with conflicting meaning.

Allowed extension patterns include:

- `aegisops.provenance.*` for AegisOps-specific collector, parser, or normalization provenance not represented cleanly in ECS
- `aegisops.identity.*` for AegisOps-specific identity correlation metadata that is not a substitute for ECS `user.*`
- `aegisops.asset.*` for AegisOps-specific asset correlation metadata that is not a substitute for ECS `host.*`, `observer.*`, `cloud.*`, or `orchestrator.*`

Disallowed extension patterns include:

- Repeating ECS values under `aegisops.*` with a conflicting or ambiguous meaning
- Using `aegisops.*` to hide missing ECS mappings that should instead use the canonical ECS field
- Treating extension fields as a reason to drop the original ECS-aligned field when that ECS field is known

## 7. Baseline Guardrails

This baseline is schema-first and runtime-neutral. A future issue may define mappings, pipelines, transforms, or storage policies, but this document does not approve those runtime behaviors.

This baseline does not approve:

- OpenSearch index mappings or analyzers
- Ingest pipeline processors or parser logic
- Field-level retention, masking, or storage layout
- Source onboarding completeness claims
- Changes to detector runtime behavior

Future runtime implementation must remain aligned to this document, `docs/secops-domain-model.md`, and the approved OpenSearch placeholder naming baseline.
