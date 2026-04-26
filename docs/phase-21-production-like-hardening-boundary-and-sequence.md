# AegisOps Phase 21 Production-Like Hardening Boundary and Sequence

## 1. Purpose

This document defines the reviewed Phase 21 production-like hardening boundary and the narrow implementation order that may follow the completed Phase 20 first live path.

It supplements `docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md`, `docs/auth-baseline.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/runbook.md`, `docs/automation-substrate-contract.md`, `docs/response-action-safety-model.md`, `docs/source-onboarding-contract.md`, `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md`, `docs/phase-17-runtime-config-contract-and-boot-command-expectations.md`, and `docs/architecture.md`.

This document defines review scope, non-expansion rules, and implementation sequencing only. It does not approve broader multi-source rollout, broad UI expansion, policy-authorized unattended execution, or new medium-risk or high-risk live actions.

## 2. Reviewed Phase 21 Hardening Boundary

The approved Phase 21 boundary is production-like hardening around the already-reviewed Phase 18 through Phase 20 path rather than a new platform breadth phase.

Phase 21 keeps the completed first live path anchored to:

`single-node Wazuh -> reviewed reverse proxy -> AegisOps control plane -> PostgreSQL -> reviewed Shuffle delegation for notify_identity_owner`

The reviewed Phase 21 hardening scope is limited to:

- authentication and authorization controls for the reviewed operator, approver, and platform administrator personas already defined in `docs/auth-baseline.md`;
- service-account ownership, credential scoping, and secret-delivery boundaries for the reviewed reverse proxy, control-plane service, Wazuh ingest path, PostgreSQL access, and reviewed Shuffle delegation path;
- reverse-proxy protections that preserve the approved ingress model, including TLS termination, access logging, authenticated webhook forwarding, and backend-only boundary credential injection;
- administrative bootstrap and break-glass access documentation narrow enough to recover or re-establish the reviewed runtime without turning direct service exposure or shared human credentials into the normal operating path;
- restore readiness for the approved control-plane runtime, PostgreSQL authority boundary, and reviewed runtime secrets and configuration inputs;
- observability that is sufficient to prove startup state, auth failures, secret-delivery failures, ingress rejections, delegation mismatches, and restore outcomes on the reviewed live path;
- topology growth conditions that define when the reviewed single-node lab boundary may expand without changing authority boundaries; and
- one reviewed second-source onboarding target that preserves identity-rich context without widening source breadth beyond the already-approved Phase 14 family order.

Phase 21 hardening is production-like because it strengthens the approved runtime boundary, access boundary, recovery posture, and visibility of the first live slice without claiming broad production-scale topology, broad automation authority, or broad source-family admission.

### 2.1 Auth, Service Accounts, and Secret Scope

Phase 21 must harden the existing operator-to-approval-to-delegation path by making identity and secret boundaries concrete before adding breadth.

The reviewed auth and secret boundary must preserve:

- attributable human identities for `Analyst`, `Approver`, and `Platform Administrator`;
- distinct machine identities for the reverse proxy, control-plane runtime, Wazuh webhook path, and reviewed Shuffle delegation path;
- secret delivery that keeps bearer secrets, backend-only proxy credentials, database credentials, and workflow credentials outside Git and outside ad hoc personal storage; and
- emergency rotation, ownership-change rotation, and scope-change rotation expectations before broader topology or source growth is attempted.

Phase 21 does not approve IdP-driven self-service role expansion, mailbox-backed service identities, shared administrator logins, source-side credentials stored in Git, or credentials that silently span monitoring, approval, workflow execution, and platform administration.

### 2.2 Reverse-Proxy, Admin Bootstrap, and Break-Glass Access

Phase 21 must preserve the reverse-proxy-first access model as the only approved user-facing ingress path.

The reviewed reverse-proxy and administrative hardening boundary includes:

- authenticated or integrity-protected webhook forwarding into the control-plane backend;
- backend-only credential injection that direct callers cannot mint;
- attributable administrative bootstrap steps for first administrative access, initial service-account provisioning, and reviewed runtime secret loading;
- a controlled break-glass access path that is disabled by default, separately documented, explicitly attributable, time-bounded, and rotated after use; and
- explicit rejection of direct long-lived backend publication, standing port-forward operations, and informal emergency admin shortcuts as the normal access model.

The break-glass path is a recovery exception only. It must not become an alternate approval path, a permanent operator shortcut, or a way to bypass the reviewed reverse proxy and control-plane authority model.

### 2.3 Restore and Observability Boundary

Phase 21 must make restore and observability specific enough to support production-like review of the existing narrow live path.

The reviewed restore boundary is limited to:

- restoring the AegisOps-owned PostgreSQL control-plane state;
- restoring the reviewed runtime configuration and secret bindings needed for the reverse proxy, control-plane service, Wazuh ingest boundary, and reviewed Shuffle delegation path;
- re-establishing enough reviewed ingress, auth, and delegation wiring to resume the completed Phase 20 notify-only live path; and
- validating restore success before normal operator use resumes.

The reviewed observability boundary is limited to:

- startup, readiness, and migration-bootstrap evidence for the control-plane runtime;
- ingress and authentication failure evidence for the reverse-proxy and Wazuh intake path;
- approval-binding, delegation, and reconciliation mismatch evidence for the reviewed Phase 20 path;
- secret-delivery and credential-rotation evidence for the reviewed machine identities; and
- restore-attempt, restore-validation, and post-restore drift evidence for the reviewed live path.

Phase 21 does not approve broad SIEM replacement analytics, broad metrics-platform rollout, after-hours autonomous operations, or observability-driven authority shortcuts that move approval or reconciliation truth outside AegisOps.

### 2.4 Topology Growth Conditions

Phase 21 does not itself approve topology growth. It defines the conditions that must be met before the reviewed single-node boundary may expand.

Phase 21 therefore defines the reviewed conditions that must be met before AegisOps grows from the current one-node operating shape toward two-node or broader deployment patterns.

Topology growth remains blocked unless the reviewed Phase 21 hardening work proves all of the following:

- auth and service-account boundaries remain attributable and least-privileged after the topology change;
- reverse-proxy-only ingress and internal-only backend exposure remain preserved;
- restore evidence covers the expanded topology components without weakening the AegisOps-owned authority boundary;
- observability remains able to distinguish ingress, auth, delegation, reconciliation, and restore failures across the expanded topology; and
- topology expansion does not make OpenSearch, n8n, Shuffle, or any source system the authority for alert, case, approval, action intent, execution, or reconciliation truth.

The reviewed topology-growth gate is therefore a one-node-to-multi-node admission review rather than pre-approval for cluster rollout.

Any topology proposal that adds production-scale breadth before these conditions are proven is out of scope for Phase 21.

### 2.5 Reviewed Second-Source Onboarding Target

The approved first reviewed second live source to onboard after the existing GitHub audit live slice is Entra ID.

The reviewed next identity-rich source order remains:

`GitHub audit -> Entra ID -> Microsoft 365 audit`

Phase 21 may define the hardening prerequisites for the reviewed second source, but it must keep second-source onboarding narrow:

- Entra ID remains audit-only and Wazuh-backed for the reviewed next live slice;
- the reviewed second-source onboarding boundary must reuse the existing control-plane contracts for payload admission, dedupe, restatement, evidence preservation, case linkage, and thin operator-surface visibility;
- no new parallel intake, case, evidence, or operator model may be introduced for the second source;
- Microsoft 365 audit remains third in the reviewed order and stays deferred during Phase 21 implementation sequencing;
- broad multi-source parallel onboarding remains out of scope; and
- no direct vendor-local actioning, source-side credential sprawl, or non-audit telemetry expansion is approved as part of this boundary.

Entra ID is the reviewed second-source target because it preserves the strongest directory and privilege context for the next identity-rich live slice without reopening broad source-family breadth.

The reviewed second-source onboarding boundary must reuse the existing control-plane contracts for payload admission, dedupe, restatement, evidence preservation, case linkage, and thin operator-surface visibility.

Phase 21 does not approve a parallel intake, evidence, case, or operator model for the second source.

## 3. Fixed Implementation Sequence

The fixed reviewed Phase 21 implementation order is:

`auth and secrets -> admin bootstrap and break-glass controls -> restore proof -> observability proof -> topology growth gate review -> Entra ID second-source onboarding`

The sequence must remain narrow because each later step depends on the earlier step proving the first live path can be trusted, recovered, and observed without widening functional scope.

### 3.1 Sequence Rules

1. `auth and secrets` comes first so the existing Phase 18 through Phase 20 runtime stops relying on placeholder identity assumptions before any new recovery, visibility, or source-admission work proceeds.
2. `admin bootstrap and break-glass controls` comes second so the reviewed operational access path is explicit before restore and observability depend on it.
3. `restore proof` comes third so the approved control-plane authority boundary can be recovered before topology or source breadth increases.
4. `observability proof` comes fourth so restore, auth, ingress, and delegation failures become reviewable instead of implicit.
5. `topology growth gate review` comes fifth and remains conditional only; it names the evidence required before any topology expansion may be reviewed later.
6. `Entra ID second-source onboarding` comes last because second-source breadth is allowed only after the existing live path is hardened, recoverable, and observable.

Phase 21 must not reorder this sequence to onboard Entra ID before auth, secrets, restore, and observability are reviewed.

## 4. Explicit Out of Scope and Non-Expansion Rules

The following remain explicitly out of scope for Phase 21:

- broad multi-source breadth beyond the reviewed GitHub audit live slice plus one reviewed Entra ID follow-on target;
- Microsoft 365 audit live onboarding in the same implementation slice as Entra ID;
- broad UI expansion, dashboard breadth, or interactive assistant growth beyond the completed thin operator surface;
- broader action catalogs, unattended execution, or any medium-risk or high-risk live action growth;
- direct vendor-local actioning for GitHub, Entra ID, or Microsoft 365;
- topology expansion that claims HA, multi-node, multi-site, or production-scale rollout as already approved; and
- any change that weakens the completed Phase 20 operator-to-approval-to-delegation path for `notify_identity_owner`.

Phase 21 preserves the completed Phase 20 first live low-risk action exactly as the current approved live path.

Phase 21 must not reopen the approved first live action, broaden Shuffle authority, bypass approval binding, or weaken reconciliation ownership in the name of hardening.

## 5. Alignment and Governing Contracts

`docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md` remains the normative source for the completed first live `notify_identity_owner` path and must not be broadened by Phase 21 hardening.

`docs/auth-baseline.md` remains the normative source for human personas, service-account ownership, credential scoping, and least-privilege expectations that Phase 21 makes concrete.

`docs/network-exposure-and-access-path-policy.md` remains the normative source for the reverse-proxy-first ingress model, webhook protection, and administrative access-path restrictions.

`docs/runbook.md` remains the normative source for restore structure and validation expectations that Phase 21 must make more concrete without implying unsupported emergency shortcuts.

`docs/automation-substrate-contract.md` and `docs/response-action-safety-model.md` remain the normative source for approval-bound delegation, idempotency, payload binding, expiry, and reconciliation requirements on the completed Phase 20 path.

`docs/source-onboarding-contract.md`, `docs/phase-14-identity-rich-source-family-design.md`, `docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md`, `docs/wazuh-alert-ingest-contract.md`, `docs/control-plane-state-model.md`, and `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md` remain the normative source for family ordering, Wazuh-backed live admission, dedupe and restatement continuity, evidence and case-linkage continuity, operator-surface visibility, and the rule that second-source onboarding must not widen into broad source breadth.

`docs/phase-17-runtime-config-contract-and-boot-command-expectations.md` and `docs/architecture.md` remain the normative source for the reviewed runtime floor, reverse-proxy-first exposure model, and AegisOps-owned authority boundary that Phase 21 hardening must preserve.
