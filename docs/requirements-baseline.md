# AegisOps

## Platform Requirements Baseline

---

## 0. Document Control

- **Version**: 0.4.0
- **Status**: Draft
- **Owner**: IT Operations, Information Systems Department
- **Last Updated**: 9 April 2026

This document defines the **non-negotiable implementation baseline** for **AegisOps** as a **governed control plane above commodity detection and automation substrates**.

Any deviation from this baseline **MUST** be documented and approved via an Architecture Decision Record (ADR) before implementation.

This document is intended to serve as both:
- a human-readable engineering baseline, and
- an execution contract for AI-assisted implementation workflows, including codex-supervisor.

---

## 1. Purpose

This project aims to design and build **AegisOps** as an internally managed SecOps platform aligned with the company’s current infrastructure, security posture, and operational maturity.

AegisOps is a governed SecOps control plane.

AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance for a narrow SMB SecOps operating model.

AegisOps owns the authoritative platform records and policy decisions for:

- Alert
- Case
- Evidence
- Observation
- Lead
- Recommendation
- Approval Decision
- Action Request
- Action Execution
- Hunt
- Hunt Run
- AI Trace
- Reconciliation

Upstream detections, findings, correlations, and product-native alerting artifacts from external substrates are treated as **Analytic Signals**.

Analytic Signals are upstream inputs to AegisOps, not the durable system of record for analyst workflow, approval state, evidence custody, action-execution state, or reconciliation.

OpenSearch, Sigma, and n8n are **not** co-equal product cores for AegisOps.
OpenSearch MAY be used as an optional or transitional analytics substrate.
Sigma MAY be used as an optional or transitional rule-definition format.
n8n MAY be used as an optional, transitional, or experimental execution substrate.

The objectives are to:

- Govern the analyst-facing lifecycle for alerts, cases, evidence, approvals, actions, hunts, and reconciliation above external substrates
- Accept and normalize upstream Analytic Signals from approved detection substrates
- Support analysts with enrichment, triage assistance, approval handling, and controlled downstream execution
- Ensure auditability, approval control, and operational transparency
- Establish a foundation that can expand over time without redefining AegisOps around one specific analytics or automation product
- Enable future collaboration with external service providers or partial outsourcing if needed without giving those systems authority over platform-owned state

> AegisOps is designed to **support human decision-making**, not to fully automate security response.

---

## 2. Scope

### 2.1 In Scope (Phase 0–1)

The following items are in scope for the initial implementation phases:

- Control-plane policy, documentation, and review baselines for alerts, cases, evidence, approvals, actions, and reconciliation
- Intake and normalization expectations for vendor-neutral Analytic Signals from approved upstream detection substrates
- Approval-gated execution expectations for approved downstream automation substrates or executors
- Optional or transitional OpenSearch-based analytics deployment at a single on-premise site
- Optional or transitional OpenSearch Dashboards usage
- Optional or transitional OpenSearch Security Analytics usage for detectors and related analytic artifacts
- Optional or transitional Sigma rule integration using a curated and reviewed subset only
- Optional, transitional, or experimental n8n workflow usage for controlled orchestration
- PostgreSQL for n8n metadata and execution state, plus the separately governed future control-plane persistence boundary
- Redis as an optional future component for queue mode
- Reverse proxy for TLS termination and controlled access
- Log ingestion pipelines, including:
  - Syslog-based ingestion
  - API-based ingestion
  - Agent-based ingestion
- Analytic-Signal-to-action-request routing with approval gating
- Documentation, validation, and operator runbooks required for maintainable implementation

### 2.2 Explicitly Out of Scope (Initial Phases)

The following items are explicitly out of scope for the initial phases:

- Full SOC automation without human approval
- Onboarding of all possible log sources
- Full HA / DR enterprise-grade clustering
- Multi-site active-active architecture
- Autonomous destructive actions (for example, automatic account disablement or network isolation)
- Multi-tenant or MSSP-style platform design
- 24/7 SOC staffing and round-the-clock human operations
- Broad endpoint remediation orchestration across all enterprise platforms
- SIEM content parity with commercial enterprise products at launch
- AegisOps will **not** rebuild Wazuh-class detection breadth in-house.
- AegisOps will **not** rebuild Shuffle-class routine automation breadth in-house.

### 2.3 Initial Operating Model

Initial phases assume a **business-hours-oriented security operations model**, not a 24/7 fully staffed SOC.

The primary deployment target is a single-company or single-business-unit deployment with roughly 250 to 1,500 managed endpoints, 2 to 6 business-hours SecOps operators, and 1 to 3 designated approvers or escalation owners.

The target operating assumption is business-hours review with explicit after-hours escalation, not a 24x7 staffed SOC.

Escalation, notification, and approval design MUST reflect this assumption.

The approved Phase 16 first-boot target is limited to the AegisOps control-plane service, PostgreSQL for AegisOps-owned state, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.

OpenSearch, n8n, the full analyst-assistant surface, the high-risk executor path, and broad source expansion remain optional, deferred, or non-blocking for first boot unless a later ADR approves a broader runtime floor.

---

## 3. Fixed Constraints

The following constraints are **mandatory** and non-negotiable.

### 3.1 Infrastructure Constraints

- AegisOps runs on an **on-premise Hyper-V cluster**
- The base operating system is **Ubuntu 24.04 LTS (fixed)**
- All applications **MUST run in Docker containers**
- Persistent data **MUST reside on storage backed by Hyper-V shared storage**
- Static IP addressing is required
- NTP synchronization is mandatory for all nodes
- Host-level manual application installation outside the approved container model is prohibited unless explicitly approved via ADR

### 3.2 Security and Operations Constraints

- Secrets **MUST NOT** be stored in Git repositories
- Environment variables, mounted secret files, or approved secret-management mechanisms MUST be used
- Controlled execution workflows performing write or destructive actions **MUST require explicit approval by default**
- Logs and audit data MUST remain within domestic storage boundaries
- Platform changes MUST be reproducible from version-controlled artifacts
- Implementation MUST favor auditability and rollback capability over convenience

---

## 4. Architecture Principles

### 4.1 Responsibility Separation

| Component / Boundary | Responsibility |
| -------------------- | -------------- |
| AegisOps control plane | Alert, case, evidence, observation, lead, recommendation, approval, action-request, action-execution, hunt, AI-trace, reconciliation, and append-only lifecycle-transition ownership |
| Upstream Analytic Signal substrates | Detection, correlation, and substrate-native alerting artifacts that feed AegisOps without becoming downstream workflow truth |
| Downstream execution substrates | Approved automation execution within the scope delegated by AegisOps |
| PostgreSQL | n8n metadata and execution state, plus the future control-plane persistence boundary under separate governance |
| Redis | Optional workflow queueing for future scaling |

Each component has a **single, clearly defined responsibility**.

No component should silently absorb another component’s responsibility without an approved architecture decision.

### 4.2 Control vs Execution

- **Detection, control, and execution MUST remain explicitly separated**
- Upstream Analytic Signal substrates perform detection or correlation only and MUST NOT directly define AegisOps-owned approval, case, or reconciliation truth
- AegisOps owns approval decisions, action intent, action-execution truth, evidence linkage, reconciliation, and the append-only lifecycle transition history paired with reviewed current-state records
- Optional execution substrates execute approved workflows only after validation and approval requirements are satisfied
- External systems MUST NOT directly trigger unrestricted execution logic
- High-risk response actions are prohibited without human oversight
- Automation MUST remain explainable and auditable
- Authoritative backup and restore workflows MUST preserve the reviewed current-state record chain together with its append-only lifecycle transition history when that history is part of the reviewed control-plane surface

### 4.3 Incremental Maturity

The architecture is intentionally designed for staged maturity:

- Phase 0: foundational deployment and limited detection
- Phase 1: analyst-assist and controlled approval-based response
- Later phases: expanded integrations and selective guarded automation

Initial implementation MUST optimize for **clarity, safety, and maintainability**, not maximum automation.

### 4.4 Reproducibility First

All core platform behavior MUST be reproducible through:

- version-controlled configuration,
- containerized deployment,
- documented parameterization, and
- repeatable validation procedures.

Manual-only procedures are unacceptable as the primary deployment or recovery mechanism.

---

## 5. Environment Baseline

### 5.1 Virtual Machine Baseline (Initial Target)

| Role | vCPU | RAM | Notes |
| ---- | ---- | --- | ----- |
| Analytics substrate (optional / transitional) | 8 | 32–64 GB | OpenSearch remains one supported example; JVM heap target approximately 50% of RAM when used |
| Execution substrate (optional / transitional) | 4 | 8–16 GB | n8n remains one supported example; sizing depends on workflow volume and integrations |
| Ingest | 4 | 8 GB | Syslog / API collectors / parsing layer |
| Proxy | 2 | 4 GB | Reverse proxy and controlled access only |

Common baseline requirements:

- OS: **Ubuntu 24.04 LTS**
- Static IP required
- NTP synchronization required
- SSH access restricted to approved administrative paths
- Sizing may be adjusted later, but only through documented change control

### 5.2 Node Roles

Initial node role naming SHOULD follow the pattern below:

- `aegisops-opensearch-node-01`
- `aegisops-opensearch-node-02` (optional / future)
- `aegisops-n8n-node`
- `aegisops-ingest-node`
- `aegisops-proxy-node`

Additional nodes MUST follow the same naming convention.

### 5.3 Parameter Baseline

Detailed operational parameters MUST be maintained separately in version-controlled parameter documents or machine-readable configuration files.

These parameters SHOULD include, at minimum:

- hostnames
- IP addresses and subnets
- storage mount points
- Docker Compose project names
- data paths
- TLS certificate paths
- backup targets
- retention defaults
- shard and replica defaults
- n8n execution mode
- queue mode enablement state

This baseline document defines policy and architecture. Detailed implementation parameters MUST be maintained as supporting artifacts.

---

## 6. Repository Structure

All AegisOps components are treated as **code assets** and MUST be managed via version control.

The repository structure and approval boundary in this document remain reviewable baseline constraints.
This rebaseline does **not** by itself approve runtime implementation changes, new adapters, or repository-structure expansion.

Recommended repository structure:

```text
aegisops/
├─ opensearch/
│  ├─ docker-compose.yml
│  ├─ index-templates/
│  ├─ detectors/
│  ├─ ilm/
│  └─ snapshots/
├─ sigma/
│  ├─ rules/
│  ├─ curated/
│  ├─ suppressed/
│  └─ mappings/
├─ n8n/
│  ├─ workflows/
│  ├─ approval-patterns/
│  ├─ credentials-template/
│  └─ webhook-contracts/
├─ postgres/
│  └─ docker-compose.yml
├─ ingest/
│  ├─ pipelines/
│  ├─ parsers/
│  └─ log-source-definitions/
├─ proxy/
│  └─ nginx/
├─ docs/
│  ├─ architecture.md
│  ├─ runbook.md
│  ├─ parameters/
│  └─ adr/
├─ scripts/
├─ config/
└─ .env.sample
````

Rules:

* Secrets MUST be excluded from repositories
* `.env.sample` files are allowed for documentation and structure only
* Real environment files MUST NOT be committed
* Ad-hoc top-level directories MUST NOT be created without approval
* Repository structure changes that affect multiple components require review

---

## 7. Naming Conventions

Consistent naming is mandatory to reduce ambiguity and improve automation reliability.

### 7.1 Product Naming

The official product name is **AegisOps**.

The name **AegisOps** SHOULD be used consistently in:

* repository names
* documentation titles
* Architecture Decision Records
* workflow references
* deployment identifiers
* operational runbooks

Examples:

* `AegisOps Platform Requirements Baseline`
* `AegisOps Repository Structure Baseline`
* `aegisops-opensearch`

### 7.2 Hostname Naming

Hostnames MUST use lowercase letters, digits, and hyphens only.

Hostnames MUST start with the `aegisops-` product namespace and SHOULD end with a stable role-specific suffix.

Where multiple hosts share the same role, hostnames SHOULD use a zero-padded ordinal suffix.

Recommended pattern:

`aegisops-<role>-node-<nn>`

Recommended examples:

* `aegisops-opensearch-node-01`
* `aegisops-opensearch-node-02`
* `aegisops-ingest-node-01`

Single-instance roles MAY omit the ordinal only when future expansion is not expected to create ambiguity.

Recommended examples:

* `aegisops-n8n-node`
* `aegisops-proxy-node`

### 7.3 Docker Compose Project Naming

Compose project names:

* MUST use the `aegisops-` prefix
* MUST use lowercase letters, digits, and hyphens only
* Service names SHOULD remain stable across environments where possible
* Container names SHOULD NOT be hard-coded unless operationally justified

Recommended examples:

* `aegisops-opensearch`
* `aegisops-n8n`
* `aegisops-ingest`
* `aegisops-proxy`

### 7.4 OpenSearch Index Naming

OpenSearch index names:

* MUST use lowercase letters, digits, and hyphens only
* MUST start with the `aegisops-` namespace
* SHOULD group data by type before source

Recommended patterns:

* `aegisops-logs-windows-*`
* `aegisops-logs-linux-*`
* `aegisops-logs-network-*`
* `aegisops-logs-saas-*`
* `aegisops-alerts-*`
* `aegisops-findings-*`

Any deviation from index naming conventions MUST be documented.

### 7.5 Detector Naming

Detector names:

* SHOULD be descriptive, stable, and namespace-prefixed
* SHOULD use lowercase letters, digits, and hyphens only

Recommended pattern:

`aegisops-<source>-<use-case>-<severity>`

Example:

`aegisops-windows-suspicious-powershell-high`

### 7.6 n8n Workflow Naming

Workflow names:

* MUST use the `aegisops_` namespace
* SHOULD follow functional prefixes
* SHOULD use lowercase letters, digits, and underscores only so they remain easy to map into exported workflow assets and automation tooling

Recommended patterns:

* `aegisops_alert_ingest_*`
* `aegisops_enrich_*`
* `aegisops_approve_*`
* `aegisops_notify_*`
* `aegisops_response_*`

Examples:

* `aegisops_alert_ingest_analytic_signals`
* `aegisops_enrich_ip_reputation`
* `aegisops_approve_host_isolation`

### 7.7 Secret and Environment Variable Naming

Secret and environment variable names:

* SHOULD be uppercase, underscore-delimited, and scoped by component
* SHOULD retain the same naming convention between environment variables and secret identifiers where practical

Examples:

* `AEGISOPS_OPENSEARCH_ADMIN_PASSWORD`
* `AEGISOPS_N8N_ENCRYPTION_KEY`
* `AEGISOPS_POSTGRES_PASSWORD`
* `AEGISOPS_PROXY_TLS_CERT_PATH`

---

## 8. Storage Policy

Storage behavior MUST be explicit and controlled.

### 8.1 General Principles

* Docker volumes MUST map to persistent storage
* Persistent runtime data MUST NOT rely on ephemeral container layers
* Primary runtime storage and backup storage MUST be logically separated
* Storage usage MUST support backup and restore operations

### 8.2 Component-Level Storage Rules

* OpenSearch data MUST reside on a dedicated persistent volume
* PostgreSQL data MUST reside on a dedicated persistent volume
* n8n configuration and state MUST be stored on persistent storage
* Proxy configuration and certificates MUST be persistently stored where required

### 8.3 Backup Separation

* Backup targets MUST be separate from primary runtime storage
* Backup location, retention, and restore ownership MUST be documented
* Snapshot retention and backup frequency MUST be parameterized

### 8.4 VM Snapshot Limitation

Hypervisor-level VM snapshots MAY be used for limited administrative purposes, but:

* they MUST NOT be treated as the primary data protection mechanism for OpenSearch or PostgreSQL,
* and they MUST NOT replace application-aware backup and restore design.

### 8.5 Restore Readiness

Each persistent component MUST have a documented restore procedure.

---

## 9. Networking Policy

Networking behavior MUST be explicit, reviewed, and consistent with the security model.

### 9.1 Access Path

* All external UI access MUST go through the approved reverse proxy
* Direct unaudited access to internal service ports is prohibited unless explicitly approved
* Administrative access paths MUST be documented

### 9.2 TLS and Transport Protection

* TLS MUST be enforced for user-facing UI access
* Webhook endpoints MUST be protected using tokens, signatures, or equivalent controls
* Internal traffic MAY initially remain plain in Phase 0 only if justified and documented
* Future hardening SHOULD consider internal TLS where operationally appropriate

### 9.3 Outbound Connectivity

* Outbound internet access SHOULD follow a deny-by-default posture unless explicitly approved
* External API dependencies MUST be documented
* Any always-on outbound dependency MUST be reviewed for operational and security impact

### 9.4 Network Segmentation

Where feasible, the following logical separation SHOULD be maintained:

* proxy/access layer
* ingest layer
* analytics/detection layer
* orchestration layer
* administration path

---

## 10. Security Baseline

Security requirements in this section are mandatory unless superseded by an approved ADR.

### 10.1 Mandatory Security Rules

* No plaintext secrets in Git
* No unreviewed production credentials in Compose files
* No use of `latest` Docker image tags
* Least-privilege access principles MUST be applied
* Audit logs MUST be retained
* Sensitive administrative operations MUST be attributable to a person or approved workflow

### 10.2 Container Security Expectations

* Container images SHOULD be version-pinned
* Digest pinning SHOULD be used where practical
* Unnecessary privileges SHOULD be removed
* Root execution inside containers SHOULD be avoided where practical
* Security-impacting exceptions MUST be documented

### 10.3 Controlled Execution Safety Rules

* Destructive or high-impact actions require approval
* All executed actions MUST be logged
* A dry-run or validation mode SHOULD exist for applicable workflows
* Response workflows MUST clearly distinguish read-only steps from write actions
* Actions affecting production systems MUST include rollback or containment guidance where applicable

---

## 11. Logging and Detection Policy

Detection quality is prioritized over detection quantity.

### 11.1 Rule Governance

* Optional Sigma-derived rules MUST NOT be deployed directly to production without review
* All rules MUST be validated in a staging environment or test index before activation
* False positives MUST be addressed through refinement, tuning, or suppression
* Detection content MUST be version controlled

### 11.2 Required Rule Metadata

Each detection rule MUST include, at minimum:

* rule title
* rule owner
* purpose
* expected behavior
* severity
* MITRE ATT&CK technique tags
* source/log prerequisites

### 11.3 Activation Standards

Before a rule is enabled in production, the following MUST be true:

* required source fields are available
* expected behavior is documented
* validation has been performed
* false-positive considerations are noted
* ownership is assigned

### 11.4 Suppression and Exception Handling

Suppression logic MUST be documented and reviewable.

Permanent suppressions without recorded rationale are prohibited.

---

## 12. Approval and Controlled Execution Model

### 12.1 Action Classification

| Class      | Examples                           | Approval Required |
| ---------- | ---------------------------------- | ----------------- |
| Read       | Lookup, enrichment, context fetch  | No                |
| Notify     | Email, Teams, Slack notification   | No                |
| Soft Write | Ticket creation, case comments     | Conditional       |
| Hard Write | Disable account, block IP, isolate | Yes (mandatory)   |

### 12.2 Approval Requirements

Approval MAY be performed through:

* AegisOps-reviewed approval interfaces exposed on the approved control-plane path
* Teams Adaptive Cards when they act as an AegisOps-reviewed approval interface rather than an independent authority surface
* other explicitly approved AegisOps-reviewed approval interfaces

Optional or transitional execution substrates, including n8n, MAY assist with downstream execution or notification handling but MUST NOT become the reviewed approval authority on the security mainline.

The following approval metadata MUST be logged:

* requester
* approver
* timestamp
* justification
* target action
* execution result

### 12.3 Conditional Soft Write Rule

Soft write actions MAY be allowed without approval only when all of the following are true:

* the action is low impact,
* the action is reversible,
* the action does not change security posture in a material way,
* and the action is explicitly classified as approval-exempt by policy.

Otherwise, the action MUST be treated as approval-required.

### 12.4 Prohibited Behavior

The following are prohibited in initial phases:

* hidden write actions inside “read-only” workflows
* approval bypass by technical implementation detail
* direct destructive actions triggered from raw inbound alerts
* undocumented write operations to production systems

---

## 13. Phased Implementation Plan

### Phase 0 – Foundation

* Core AegisOps platform deployment
* Limited log source onboarding
* Detection plus notification only
* Initial validation of repository structure, deployment model, and approval pattern

### Phase 1 – Assisted Response

* Curated optional or transitional detection-content onboarding
* Approval-based controlled execution workflows
* Lightweight incident tracking
* Controlled enrichment and analyst-support automation

### Phase 2 – Expansion (Future)

* Deeper SaaS integration (for example, Cato, Okta, AWS)
* Partial automated response with safeguards
* Optional collaboration with external SOC providers
* Scaling and resilience improvements as justified by usage and risk

---

## 14. Change Management

Architecture and implementation changes MUST be governed explicitly.

### 14.1 ADR Requirement

Any change affecting architecture, boundaries, naming, security posture, storage layout, or operational model MUST be proposed through an ADR before implementation.

### 14.2 Separation of Design and Implementation

* Design-change issues and implementation issues MUST be kept separate
* Implementation issues MUST NOT silently redefine architecture
* Cross-cutting parameter changes MUST be reviewed before merge

### 14.3 No Silent Drift

Silent design drift is prohibited.

If implementation reveals a flaw in the current baseline, that flaw MUST be resolved through formal review, not hidden within code changes.

---

## 15. Quality Requirements

All implementations MUST:

* be reproducible through Docker-based deployment artifacts,
* be version controlled,
* include documentation updates,
* include validation or verification steps,
* avoid manual-only operational dependency,
* and be reviewable by another engineer or reviewer.

Quality gates SHOULD favor maintainability and operational safety over speed.

---

## 16. Definition of Done

An issue is considered complete only when all of the following are true:

* the behavior delta is implemented as scoped,
* the implementation complies with this baseline,
* documentation is updated where applicable,
* validation steps are documented and pass,
* rollback or recovery notes are added where applicable,
* no forbidden shortcut has been introduced,
* and review has been completed.

Partial technical completion without documentation or validation is not considered done.

---

## 17. Forbidden Shortcuts

The following shortcuts are explicitly prohibited unless approved by ADR:

* using `latest` Docker image tags
* hardcoding secrets or credentials
* committing real environment files to Git
* adding ad-hoc directories or volume paths outside the defined structure
* enabling production detection rules without validation
* implementing write-capable workflows without explicit policy treatment
* bypassing reverse proxy access controls without approval
* relying on undocumented manual steps as the primary operational method
* hiding architecture changes inside implementation-only issues

---

## 18. Design Rationale

AegisOps intentionally avoids full autonomous response in early phases.

Key design priorities are:

* operational clarity
* human accountability
* audit readiness
* incremental automation
* long-term extensibility
* controlled risk exposure

This approach reduces operational risk while enabling continuous maturity.

AegisOps is intended to evolve deliberately, not opportunistically.

---

## 19. References

The following references SHOULD be maintained and kept current:

* Approved substrate documentation for the current analytics and execution path
* OpenSearch official documentation when OpenSearch is in approved use
* SigmaHQ official repository and documentation when Sigma is in approved use
* n8n official documentation when n8n is in approved use
* Internal ADR repository
* Internal runbooks
* Internal parameter baseline documents
* Internal security standards and approval procedures

---

### End of Document
