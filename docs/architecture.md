# AegisOps Architecture Overview

This document summarizes the approved baseline architecture for AegisOps.

It supplements `docs/requirements-baseline.md` with a concise overview of component roles, trust boundaries, and access expectations for reviewers and future implementation work.

This document describes the approved baseline only and does not introduce runtime changes.

## 1. Purpose

This overview exists to make the approved high-level architecture explicit before detailed implementation expands around it.

It defines:

- the primary platform components,
- the responsibility boundary for each component,
- the separation between detection and workflow execution,
- the approved high-level access model, and
- the baseline assumptions that future issues must preserve unless an ADR approves a change.

## 2. Architecture Overview

AegisOps is an internally managed SOC and SOAR platform built around a small number of clearly separated roles.

At a high level, data enters through the ingest role, is stored and analyzed in OpenSearch, is matched against reviewed Sigma-derived detection content, and then flows into n8n for enrichment, approval handling, routing, and controlled downstream actions.

Supporting services exist to preserve those boundaries rather than to blur them. PostgreSQL holds n8n state, Redis remains optional for future queue-based scaling, and the proxy is the controlled access point for user-facing interfaces.

## 3. Component Responsibilities and Boundaries

OpenSearch is the SIEM core for log ingestion, storage, search, analytics, and detection.

Its approved boundary is analytics and detection. It is not the place for response execution logic, approval handling, or ad-hoc orchestration behavior.

Sigma defines detection logic only and is not a runtime execution engine.

Its role is to provide standardized, reviewable detection definitions that can be translated into approved detection content without taking on storage, orchestration, or response responsibilities.

n8n handles enrichment, routing, orchestration, approval workflows, and downstream integration.

Its approved boundary is controlled workflow execution and integration handling after alerts or findings have been validated and routed into the SOAR layer.

PostgreSQL stores n8n metadata and execution state.

It supports workflow persistence and operational state for n8n, but it is not a substitute analytics store or a general-purpose platform data lake.

Redis is reserved for optional future workflow queueing and future scaling.

It is not required for the initial baseline and should be understood as a bounded supporting component for later queue-mode operation rather than a new control surface.

The proxy provides TLS termination and controlled user-facing access.

Its approved role is ingress for user-facing UI access and related access controls, not backend analytics, workflow execution, or direct data processing.

The ingest role handles syslog, API-based, and agent-based collection and parsing before data reaches analytics systems.

Its approved boundary is collection and preparation of incoming telemetry rather than long-term analytics, approval logic, or operator-facing UI responsibilities.

## 4. Control Plane vs Execution Plane

Detection and execution remain strictly separated in the approved baseline.

OpenSearch performs detection and analytics only and must not directly execute response actions.

Sigma remains part of the control logic for defining what should be detected, but it does not execute workflows and does not perform runtime actions itself.

n8n may execute approved workflows only after validation and approval requirements are satisfied.

This means the decision to detect, the decision to approve, and the act of execution are intentionally reviewable steps rather than a single opaque automation path.

The approved baseline therefore treats analytics and detection as one plane of responsibility, while workflow execution and downstream action handling remain in a separate orchestration plane under explicit control.

## 5. Approved Access Model

All external UI access must traverse the approved reverse proxy.

The proxy is the approved entry point for user-facing interfaces such as OpenSearch Dashboards, the n8n UI, and similar future web surfaces that may be introduced within the baseline.

Direct unaudited exposure of internal service ports is not part of the approved baseline.

OpenSearch cluster interfaces, PostgreSQL, Redis, ingest services, and similar backend components remain internal by default and should be reached only through approved internal or administrative paths.

Administrative access must remain documented and consistent with the baseline network exposure policy. This overview does not authorize alternative ingress paths, direct publication of backend services, or always-on outbound dependencies beyond separately reviewed policy.

## 6. Baseline Alignment Notes

This overview reflects the current approved baseline and must not be used to infer unapproved architecture changes.

In particular, it does not introduce multi-site design, unrestricted automation, tenant isolation changes, new data stores, or additional externally exposed service roles.

Any future change to component boundaries, approval behavior, access paths, storage responsibilities, or operating model still requires explicit review through the project’s ADR and baseline governance process.
