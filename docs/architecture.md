# AegisOps Architecture Overview

This document summarizes the approved baseline architecture for AegisOps.

It supplements `docs/requirements-baseline.md` with a concise overview of component roles, trust boundaries, and access expectations for reviewers and future implementation work.

This document describes the approved baseline only and does not introduce runtime changes.

## 1. Purpose

This overview exists to make the approved high-level architecture explicit before detailed implementation expands around it.

It defines:

- the primary architecture layers,
- the responsibility boundary for each layer,
- the mainline policy-sensitive path across those layers,
- the separation between governance, automation, and execution, and
- the baseline assumptions that future issues must preserve unless an ADR approves a change.

## 2. Architecture Overview

AegisOps is a governed SecOps control plane above external detection and automation substrates.

AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners.

The target operating assumption is business-hours review with explicit after-hours escalation, not a 24x7 staffed SOC.

The approved baseline is organized around four roles:

- the detection substrate,
- the AegisOps control plane,
- the routine automation substrate, and
- the controlled execution surface.

The initial standard detection substrate is Wazuh.

The initial standard routine automation substrate is Shuffle.

The AegisOps control plane is the authoritative owner of policy-sensitive records, approval decisions, evidence linkage, action intent, and reconciliation truth across substrate boundaries.

The controlled execution surface is the isolated executor path for higher-risk actions that require tighter execution controls than routine automation should own.

The normative mainline policy-sensitive path is:

`Substrate Detection Record -> Analytic Signal -> Alert or Case -> Action Request -> Approval Decision -> Approved Automation Substrate or Executor -> Reconciliation`

That path must remain explicit, reviewable, and auditable.

Direct substrate-to-automation shortcuts must not become the policy-sensitive system-of-record path.

Detection substrates may emit substrate detection records and analytic signals, and automation substrates may perform delegated work, but neither may become the authority for alert truth, case truth, approval truth, action intent, evidence custody, or reconciliation truth.

OpenSearch, Sigma, and n8n may still appear in the repository structure as optional, transitional, or experimental components, but they are no longer the product core in the approved architecture baseline.

## 3. Component Responsibilities and Boundaries

### Detection Substrate

The detection substrate is responsible for telemetry analysis, detection generation, correlation, and substrate-native alerting artifacts.

Wazuh is the initial standard detection substrate in the approved baseline.

Its approved boundary is upstream detection and analytic-signal production.

The detection substrate must not directly own cases, approval decisions, evidence truth, or execution truth for AegisOps-governed workflows.

OpenSearch may still be used as an optional or transitional analytics substrate.

Sigma may still be used as an optional or transitional rule-definition format or translation source.

Those tools remain subordinate to the approved control-plane boundary and must not redefine the architecture narrative around themselves.

### AegisOps Control Plane

The AegisOps control plane is the authoritative decision and execution governance layer.

It owns the platform records and policy decisions for alerts, cases, evidence, observations, leads, recommendations, approval decisions, action requests, hunts, hunt runs, AI traces, and reconciliation.

Its approved boundary includes policy evaluation, approval handling, evidence linkage, execution delegation, and cross-substrate reconciliation.

It is the authoritative system of record for policy-sensitive workflow state.

Neither detection substrates nor automation substrates may bypass this boundary and become the durable authority path for AegisOps-owned workflow truth.

### Routine Automation Substrate

The routine automation substrate performs approved automation that the control plane delegates within bounded scope.

Shuffle is the initial standard routine automation substrate in the approved baseline.

Its approved boundary is routine enrichment, routing, integration handling, and approved automation execution after the control plane has produced the governing action request and approval decision context.

The routine automation substrate must not mint or overwrite approval truth, action intent, evidence truth, or reconciliation truth.

n8n may still be used as an optional, transitional, or experimental executor or orchestration substrate.

That status does not make it a product core or an authority surface.

### Controlled Execution Surface

The controlled execution surface is the isolated executor path for higher-risk actions.

Its approved boundary is tightly controlled action execution under the authority of the AegisOps control plane.

The executor is an execution surface, not a policy engine and not a workflow system of record.

It receives bounded, approved intent from the control plane and returns execution outcomes for reconciliation.

Implementation of executor code, substrate connectors, and UI work remains out of scope for this architecture baseline.

## 4. Control Plane vs Execution Plane

Detection, control, automation, and execution remain explicitly separated in the approved baseline.

Detection substrates perform detection and correlation only.

The AegisOps control plane owns the policy-sensitive path from analytic signal intake through alert or case state, action request generation, approval decisions, and reconciliation.

Routine automation substrates execute delegated automation only after control-plane validation and approval requirements are satisfied.

The controlled execution surface handles higher-risk actions only within the explicit authority and safety controls defined by the control plane.

This means the decision to detect, the decision to approve, and the act of execution are intentionally reviewable steps rather than a single opaque automation path.

The approved baseline forbids direct substrate-to-automation shortcuts from becoming the mainline policy-sensitive path, even if such shortcuts appear operationally convenient.

Substrate-native records may support observability or local operations, but they must not displace the AegisOps control plane as the authority for approval, evidence, and reconciliation truth.

## 5. Approved Access Model

All external UI access must traverse the approved reverse proxy.

The proxy is the approved entry point for user-facing interfaces such as Wazuh, Shuffle, OpenSearch Dashboards, n8n, and similar future web surfaces that may be introduced within the baseline.

Direct unaudited exposure of internal service ports is not part of the approved baseline.

Detection substrates, automation substrates, PostgreSQL, Redis, ingest services, the executor, and similar backend components remain internal by default and should be reached only through approved internal or administrative paths.

Administrative access must remain documented and consistent with the baseline network exposure policy.

This overview does not authorize alternative ingress paths, direct publication of backend services, or always-on outbound dependencies beyond separately reviewed policy.

## 6. Baseline Alignment Notes

This overview reflects the current approved baseline and must not be used to infer unapproved architecture changes.

In particular, it does not introduce live substrate connectors, executor implementation, schema rollout, unrestricted automation, multi-site design, tenant-isolation changes, new data stores, or additional externally exposed service roles.

Future substrate substitutions remain possible, but they must preserve the AegisOps-owned authority boundary for approval, evidence, action intent, and reconciliation unless a later ADR explicitly changes that governance model.

Any future change to component boundaries, approval behavior, access paths, storage responsibilities, or operating model still requires explicit review through the project's ADR and baseline governance process.
