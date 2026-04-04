# AegisOps Safe Query Gateway and AI Hunt Tool Policy

## 1. Purpose

This document defines the baseline Safe Query Gateway and tool policy for future AI-assisted hunt workflows.

It supplements `docs/requirements-baseline.md`, `docs/architecture.md`, `docs/control-plane-state-model.md`, `docs/auth-baseline.md`, and `docs/adr/0001-phase-7-ai-hunt-plane-and-external-ai-data-boundary.md` by making bounded read behavior explicit before any live AI-hunt implementation exists.

This document defines request, validation, and trust-boundary policy only. It does not authorize direct AI access to OpenSearch, unrestricted public web access, or execution-capable tools.

## 2. Safe Query Gateway Boundary

The Safe Query Gateway is the only approved path for AI-assisted hunt reads that touch internal analytics backends or other bounded read tools.

AI-authored free-form queries must never be executed directly against OpenSearch, SQL engines, shell surfaces, or public-internet search tools.

The gateway exists to keep the AI hunt plane advisory-only even when it helps analysts form questions about internal data.

The gateway therefore owns request normalization, validation, deterministic query generation, budget enforcement, result shaping, and citation attachment before any backend call is attempted.

Backend-specific syntax, unreviewed operator text, and model-generated search expressions are input material to reject or reinterpret through policy, not privileged instructions to execute.

## 3. Structured Query Intent Contract

Every hunt request must be expressed as structured query intent rather than raw query text.

At minimum, structured query intent must carry:

| Field | Required purpose |
| ---- | ---- |
| Intent identifier | Distinguishes one request from retries, edits, or later follow-up hunts. |
| Hunt family | Selects the approved template family and the associated allowlist policy. |
| Analyst or workflow requester identity | Preserves who asked the question and under which bounded authority. |
| Data source class | Declares whether the request targets internal-only reads, approved-partner reads, or another explicit trust boundary. |
| Index or dataset selector | Names the allowlisted logical source to query rather than embedding backend-native syntax. |
| Time window | Carries explicit start and end timestamps so the time cap can be enforced deterministically. |
| Requested filters | Declares approved field-value conditions using normalized field identifiers, not backend query language fragments. |
| Requested projections | States which fields may appear in the result shape, limited to approved readable fields. |
| Sort or ranking mode | Chooses from allowlisted deterministic result ordering modes only. |
| Row cap request | Requests a bounded maximum row count that cannot exceed policy. |
| Aggregation request | Declares whether aggregation is requested and which approved grouping or metric template is intended. |
| Citation mode | States which citation-bearing result shape is required for the requested observation type. |

Structured query intent must reject free-form clauses such as arbitrary DSL, Lucene fragments, SQL snippets, shell pipes, or user-supplied regular-expression payloads unless a future approved template narrows exactly how that syntax is encoded and validated.

## 4. Validation and Deterministic Query Generation

The gateway must compile validated intent into deterministic query templates owned by AegisOps rather than passing model-authored syntax through to a backend.

Deterministic generation means the same approved intent and same parameter values always produce the same backend request shape, field projection, sort behavior, and citation metadata plan.

Validation must reject requests that exceed allowlisted index scope, approved field access, bounded time range, row cap, aggregation policy, or query cost budget.

Validation must happen before backend execution and must include at minimum:

- intent schema validation for required fields and enum values;
- allowlist checks for hunt family, index scope, readable fields, sort modes, and aggregation modes;
- bounded time-range checks against the fixed time cap for the selected hunt family;
- row-cap enforcement before any result window is requested from the backend;
- deterministic cost-budget estimation using the selected indices, time window, requested filters, row count, and aggregation mode; and
- trust-boundary checks that confirm the requested tool class is permitted for the current workflow and requester context.

Compiled backend requests must remain owned by repository-reviewed templates or code paths, not by model-authored strings assembled at runtime.

If the backend cannot satisfy the approved intent with a deterministic template, the request must be rejected rather than widened into an ad hoc backend query.

## 5. Allowlists and Budget Limits

The gateway must encode its safety policy through explicit allowlists and hard limits instead of best-effort prompt instructions.

| Control | Policy |
| ---- | ---- |
| `Index scope` | Only explicitly allowlisted indices or data views for the approved hunt family may be queried. |
| `Time range` | Every request must carry a bounded start and end time, and the policy must enforce a fixed time cap. |
| `Field access` | Requested filters, projections, sort keys, and grouping fields must come from an allowlist tied to the hunt family. |
| `Row cap` | The gateway must enforce a maximum result window and refuse unbounded result retrieval. |
| `Aggregation` | Aggregations are denied by default and may be enabled only for approved templates with bounded cardinality. |
| `Cost budget` | Each request must stay within a deterministic query-cost budget before execution is attempted. |

The allowlist must be specific enough that a reviewer can answer all of the following for any approved hunt family:

- which indices or logical datasets may be read;
- which fields may be filtered, projected, sorted, or grouped;
- the maximum time cap and maximum row cap;
- whether aggregation is disallowed, bucket-limited, or metric-limited; and
- how the cost budget is computed and what rejection threshold applies.

Aggregation requires separate caution because it can widen visibility and hide expensive cardinality explosions behind apparently simple prompts.

When aggregation is allowed, the policy must define the exact approved grouping fields, the maximum bucket count, the allowed metric family, and the citation format for each returned bucket.

## 6. Citation-Bearing Response Contract

The gateway must return bounded observations rather than unconstrained prose summaries.

Returned observations must carry citations that let an analyst trace each statement back to the underlying index, document identifier or bucket key, and query window used to produce it.

At minimum, each returned observation must preserve:

| Response field | Required citation role |
| ---- | ---- |
| Observation identifier | Lets later notes and reviews refer to one bounded result item. |
| Observation text or structured value | States the finding in analyst-readable form without losing the original bounded shape. |
| Source index or dataset | Shows which approved source produced the observation. |
| Document identifier, event identifier, or bucket key | Lets the analyst trace the observation to the underlying record set or aggregate bucket. |
| Query window | Preserves the exact start and end time used for the backend request. |
| Field path references | Identifies which fields were read to derive the statement. |
| Query template identifier and template version | Proves which deterministic query shape produced the result. |
| Retrieval timestamp | Records when the gateway executed the request. |

A response without sufficient citations must be treated as advisory text only and must not be promoted to evidence, case facts, or approval context.

If the gateway produces any narrative summary, that summary must remain explicitly derivative of the cited observations rather than a replacement for them.

The response contract must also preserve truncation signals so analysts can tell when the returned observation set was row-capped, bucket-capped, or otherwise intentionally bounded.

## 7. Tool Policy Trust Classes

Read tools must not be treated as equally safe merely because they do not mutate data.

Trust class defines the data-egress and authority boundary crossed by a read, and future implementations must attach policy to that trust boundary explicitly.

| Trust class | Allowed source family | Boundary expectation |
| ---- | ---- | ---- |
| `Internal-only read` | Approved internal AegisOps data sources such as OpenSearch findings, normalized event stores, or internal case metadata. | No public-internet access and no provider egress beyond the approved internal boundary. |
| `Approved-partner read` | Bounded reads to named external services under contract or delegated trust, such as ticketing, threat intel, or CMDB APIs. | Egress is allowed only to explicitly approved partners with scoped fields, request logging, and ownership. |
| `Public-internet read` | Searches or retrieval against public web content outside approved partner boundaries. | Disabled by default for hunt workflows and must be modeled as a separate trust boundary with explicit approval if ever enabled later. |

`Internal-only read` is the default design target for the Safe Query Gateway because it preserves the narrowest trust boundary and keeps evidence-bearing data inside AegisOps-controlled systems.

`Approved-partner read` must remain separately reviewed because even read-only egress can disclose internal hunt focus, operational identifiers, or case context to an external party.

`Public-internet read` must not be silently bundled into hunt assistance, citations, or enrichment logic. If a future issue proposes it, that path requires its own policy, its own approval surface, and explicit operator labeling that the result crossed a broader trust boundary.

## 8. Failure Handling

Validation failure must return a machine-readable rejection reason that identifies which policy boundary was crossed without silently widening the request.

Typical rejection classes include invalid intent shape, disallowed index scope, disallowed field access, time cap exceeded, row cap exceeded, aggregation not allowed, cost budget exceeded, trust-boundary mismatch, and citation plan unavailable.

Timeouts, partial backend failures, missing citations, or over-budget results must fail closed rather than returning uncited speculative summaries.

Failure handling must preserve the difference between:

- a request rejected before execution because it violated policy;
- a backend execution that started but did not return a valid bounded result;
- a response that returned data but could not satisfy citation requirements; and
- an over-budget or over-broad result that must be truncated and labeled or rejected under policy.

The gateway must not compensate for invalid intent by broadening index scope, widening the time window, dropping filters, or switching to a looser trust class.

## 9. Baseline Alignment Notes

This policy preserves the baseline separation between analytics, advisory AI assistance, approval state, and execution surfaces while making data egress risk explicit by trust class.

It aligns with the requirements baseline rule that auditability and rollback safety take priority over convenience, with the architecture rule that OpenSearch remains an analytics surface rather than an AI-execution endpoint, and with ADR-0001's rule that AI assistance remains citation-first and advisory-only.

It also prevents future implementation from treating backend query syntax, public-web tooling, or read egress across trust boundaries as harmless just because no immediate write occurs.
