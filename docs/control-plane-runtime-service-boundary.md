# AegisOps Control-Plane Runtime Service Boundary

This document defines the approved runtime boundary and repository placement for the first live AegisOps control-plane service.

It supplements `docs/control-plane-state-model.md` and `docs/repository-structure-baseline.md` by defining where live control-plane application code belongs and how that service relates to OpenSearch, n8n, and PostgreSQL.

This document approves the first live service boundary only. It does not approve an analyst UI, unrestricted runtime expansion, direct response execution, or any new top-level repository area beyond the approved `control-plane/` home described here.

## 1. Purpose

Phase 9 needs a live AegisOps-owned control-plane service that can materialize authoritative platform state without collapsing that authority back into OpenSearch documents or n8n runtime metadata.

This boundary exists so future implementation can scaffold the first live service without inventing a new repository home, changing the ownership split, or turning persistence placeholders into the application boundary by accident.

## 2. Approved Runtime Boundary

The first live control-plane service owns AegisOps-authored application behavior for authoritative control-plane records and reconciliation logic.

Its approved responsibilities are:

- ingesting or accepting reviewed upstream analytic signals and converting them into AegisOps control-plane records under the approved state model;
- assigning and preserving AegisOps control-plane identifiers and lifecycle state instead of reusing OpenSearch document identity or substrate-local execution identity as the primary key;
- persisting authoritative control-plane records in the AegisOps-owned PostgreSQL boundary described by `docs/control-plane-state-model.md` and reserved under `postgres/control-plane/`;
- reconciling upstream OpenSearch signals and downstream automation-substrate or executor outcomes against authoritative control-plane intent; and
- exposing internal service-local application interfaces needed to create, update, query, and reconcile control-plane records.

The first live control-plane service does not own telemetry ingestion, SIEM analytics, detection execution, workflow execution, or connector-specific action logic.

OpenSearch remains the system of record for telemetry, findings, and OpenSearch-native analytic artifacts.

n8n remains the system of record for workflow runtime metadata, step execution, retry behavior inside a running workflow, and connector-local execution details.

`postgres/control-plane/` remains the persistence contract home for reviewed schema and migration assets, but it is not the repository home for live control-plane application code.

## 3. Repository Placement and Local Runtime Shape

The approved repository home for live control-plane application code is the top-level `control-plane/` directory.

That directory exists so implementation can add the first live service without inventing another top-level runtime area later.

The approved split is:

- `control-plane/` contains live application code, service bootstrapping, internal APIs, adapters, tests, and service-local documentation for the AegisOps-owned runtime boundary.
- `postgres/control-plane/` contains the reviewed PostgreSQL persistence contract, including schema and migration assets for the AegisOps-owned control-plane datastore boundary.

The local runtime shape under `control-plane/` must keep the following concerns inside the same service root:

- application entrypoints and bootstrapping for the live control-plane service;
- control-plane domain and lifecycle logic for AegisOps-owned records;
- adapters for PostgreSQL persistence, OpenSearch signal intake, and n8n reconciliation inputs; and
- focused tests for those boundaries.

Language-specific file layout under `control-plane/` may be chosen by the implementation issue, but the runtime must remain rooted there rather than being spread across `opensearch/`, `n8n/`, or `postgres/`.

## 4. Phase 9 Included Capabilities

Phase 9 includes the minimum live control-plane runtime needed to make AegisOps authoritative over its own platform records.

Included capabilities are:

- a live internal control-plane service rooted under `control-plane/`;
- materialization of authoritative AegisOps control-plane records in the approved PostgreSQL-backed boundary;
- explicit ingestion or synchronization logic for upstream OpenSearch findings or alert-like analytic signals into control-plane-owned records;
- explicit reconciliation logic that can compare control-plane intent with reviewed automation-substrate or executor outcomes using stable identifiers; and
- repository-local service scaffolding that preserves the ownership split already approved by the state-model baseline.

## 5. Explicit Non-Goals

The following remain out of scope for this first live control-plane service boundary:

- analyst UI or case-management frontend surfaces;
- live telemetry expansion or source-onboarding growth;
- AI runtime features, prompt execution, or AI-driven workflow authority;
- write-capable response execution or direct replacement of n8n as the execution plane;
- replacing OpenSearch as the analytics and detection plane; and
- collapsing control-plane authority into OpenSearch indexes, OpenSearch documents, n8n execution metadata, or ad hoc repository-local seed files.

## 6. System Relationships and Ownership Split

The first live control-plane service sits between OpenSearch and n8n rather than inside either product.

Its approved relationship to each system is:

- OpenSearch provides upstream findings, alerts, and analytic context that the control-plane service consumes as signals rather than as downstream state authority.
- The control-plane service owns alert, case, evidence, observation, lead, recommendation, approval, action-request, hunt, hunt-run, AI-trace, and reconciliation state according to `docs/control-plane-state-model.md`.
- PostgreSQL provides the AegisOps-owned persistence boundary for those control-plane records, with reviewed schema and migration assets remaining under `postgres/control-plane/`.
- n8n provides workflow execution and connector-local runtime behavior that the control-plane service correlates and reconciles without treating n8n metadata as the authoritative record of approval, intent, or case lifecycle.

The approved service boundary therefore fails closed if future implementation attempts to:

- place live control-plane application code under `postgres/control-plane/`;
- treat OpenSearch documents as the authoritative alert or case record;
- treat n8n execution history as the authoritative approval or action-request record; or
- introduce a second top-level application home for the same control-plane service.

## 7. Alignment Notes

`docs/control-plane-state-model.md` remains the normative source for record families, identifiers, lifecycle expectations, and ownership rules.

`docs/repository-structure-baseline.md` remains the normative source for approved top-level repository placement, including the dedicated `control-plane/` runtime home and the separate `postgres/control-plane/` persistence contract home.

Within the approved Phase 16 release-state, the first-boot runtime target for this boundary is limited to the control-plane service, the reviewed PostgreSQL persistence dependency, the approved reverse proxy ingress boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

That first-boot target does not make OpenSearch, n8n, the full analyst-assistant surface, or the high-risk executor path mandatory startup blockers.

Later implementation may choose a concrete language, framework, and internal package layout, but it must preserve the service boundary and repository placement approved here.
