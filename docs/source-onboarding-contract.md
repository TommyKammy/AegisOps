# AegisOps Source Onboarding Contract

## 1. Purpose

This document defines the minimum onboarding contract for any telemetry source family that seeks admission into the AegisOps normalized telemetry baseline.

It establishes the required evidence, ownership, field coverage, provenance, and readiness checks that must exist before downstream detection content can rely on a source family.

This contract governs documentation and validation expectations only. It does not approve live ingestion, parser deployment, source credentials, or runtime onboarding behavior.

## 2. Contract Scope and Non-Goals

The contract applies to source families rather than one-off products or ad hoc integrations.

Each source family onboarding package must identify the source family description, parser ownership, raw payload reference, normalization mapping, and sample data plan.

This contract does not approve live collector enrollment, parser rollout, source-side credentials, or production activation of detectors.

This contract also does not require every future source family to be detection-ready immediately. It requires every source family to declare its current readiness state and evidence gaps explicitly.

## 3. Minimum Onboarding Package

Every source family onboarding package must provide the minimum artifacts below before review can treat the family as schema-reviewed.

| Artifact | Expectation |
| ---- | ---- |
| Source family description | Required artifact |
| Parser ownership and lifecycle | Required artifact |
| Raw payload reference | Required artifact |
| Normalization mapping | Required artifact |
| Sample data and replay plan | Required artifact |

Minimum package interpretation:

- The source family description must explain the family boundary, what products or event classes it covers, and why it belongs to one canonical family rather than another.
- Parser ownership and lifecycle must identify the owning team or maintainer, the parser implementation boundary, and how versioned parser changes will be reviewed.
- Raw payload reference must point to representative source-native records or wrapped ingest-boundary records that preserve original source meaning.
- Normalization mapping must show how source-native fields map into the canonical telemetry schema and where values remain source-specific under approved provenance or extension rules.
- Sample data and replay plan must define the approved validation corpus for future parser and mapping checks without implying live ingestion approval.

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

Detection-ready review must also confirm the following:

- The normalization mapping uses canonical schema semantics first and reserves `aegisops.*` extensions for additive cases that ECS does not already cover.
- Required field groups from the canonical telemetry schema remain required even when a source family cannot yet satisfy them.
- Shared required field groups that are unavailable block normalization unless the onboarding package documents an approved exception path.
- Family required baseline coverage that is unavailable or intentionally deferred blocks detection-ready status unless the onboarding package documents an approved exception path and the resulting detector-use limits.
- Timestamp quality limitations are preserved as evidence rather than hidden by silently rewriting source meaning.
- Identity and asset linkage claims are supported by actual source fields, not by fabricated enrichment assumptions.
- Detection authors can determine exactly which normalized fields are stable enough to depend on before activating rule content for the family.

## 5. Replay and Sample Data Expectations

Replay-capable sample data must be sufficient for future parser and mapping validation without implying that live source onboarding is approved.

Sample datasets must preserve provenance, capture representative success and failure cases, and document any redaction or synthetic substitutions.

Sources that are not yet detection-ready must state their explicit non-goals, known schema gaps, and why downstream detections must not depend on them yet.

Replay and sample-data expectations include:

- At least one representative raw payload set for normal successful parsing and one set for malformed, partial, or edge-case records when those cases matter to schema coverage.
- Documentation of whether samples are vendor-provided examples, internally captured payloads, synthetic fixtures, or redacted operational records.
- Sufficient examples to validate field coverage, timestamp behavior, provenance preservation, and identity or asset linkage claims for the family.
- Clear notes when a source family is admitted only as a future candidate so replay assets exist for design work but not for live onboarding.

## 6. Readiness States

Readiness states must distinguish at least `candidate`, `schema-reviewed`, and `detection-ready` source families.

State expectations:

- `candidate` means the family is recognized, scoped, and documented enough to reserve a future onboarding path, but detection content must not depend on it.
- `schema-reviewed` means the minimum onboarding package exists and the canonical mapping and evidence gaps have been reviewed, but detection activation remains blocked until readiness evidence is complete.
- `detection-ready` means the family has completed the required evidence package, has no unresolved intentionally deferred required coverage, and may be referenced by future detection content subject to separate detector and rollout review.
- `detection-ready` may rely on an explicit exception path only when the exception states which required coverage is missing, why the gap does not block the approved readiness scope, and which downstream detections remain prohibited.

This contract is schema-driven and family-oriented. It must not become source-specific ad hoc guidance for individual products.

## 7. Baseline Alignment Notes

This contract remains aligned to `docs/canonical-telemetry-schema-baseline.md` and does not approve runtime parsers, ingest pipelines, or credential handling.

It also remains aligned to `docs/secops-domain-model.md` by treating normalized telemetry readiness as distinct from detection activation, alert routing, approval workflows, and response execution.

Future implementation work may add parser code, replay tooling, or source-specific assets, but those changes require separate approved issues and must continue to satisfy this onboarding contract.
