# AegisOps

**AegisOps** is a governed SecOps decision and execution control plane above reviewed detection and automation substrates.

It is **not** a SIEM/SOAR replacement.
It is the layer that owns the authoritative record chain for analyst work, approval, delegation, execution, and reconciliation.

Initial standard substrates:

- **Wazuh** — reviewed detection substrate and upstream signal source
- **Shuffle** — reviewed routine automation substrate for approved low-risk actions

Current optional / transitional assets:

- **OpenSearch** — optional analytics and enrichment extension, not the product core
- **Sigma** — optional research / prototyping rule asset, not the product core
- **n8n** — optional / transitional orchestration asset, not the mainline security path

---

## What AegisOps is

AegisOps takes upstream security signals and turns them into an operator-trustworthy record chain:

`Analytic Signal -> Alert -> Case -> Evidence -> Recommendation -> Action Request -> Approval -> Delegation -> Action Execution -> Reconciliation`

The core idea is simple:

- upstream tools may detect or execute,
- but **AegisOps owns the authoritative truth** for policy-sensitive workflow state.

That means:

- alerts and cases are AegisOps records
- evidence custody is explicit
- approvals are first-class records
- execution is separate from approval
- downstream workflow success does not automatically become control-plane truth
- reconciliation mismatch is preserved instead of silently normalized away

---

## What AegisOps is not

AegisOps is **not**:

- a self-built replacement for all SIEM features
- a self-built replacement for all SOAR features
- a broad autonomous response platform
- a broad source-coverage platform trying to rebuild Wazuh-class breadth
- an AI-first SOC that lets an assistant become approval or execution authority

---

## Current mainline architecture

### Mainline components

| Layer | Mainline component | Responsibility |
| --- | --- | --- |
| Detection substrate | Wazuh | Produces reviewed upstream substrate detection records |
| Control plane | AegisOps Control Plane Runtime | Owns analytic-signal admission, alert/case/evidence/recommendation/action/reconciliation truth |
| Automation substrate | Shuffle | Executes reviewed delegated low-risk automation only |
| Persistence | PostgreSQL | Authoritative AegisOps control-plane record store |
| Access boundary | Reverse Proxy | Approved ingress, auth boundary, readiness surface |

### Optional / transitional components

| Component | Current role |
| --- | --- |
| OpenSearch | Optional analytics / hunting / secondary assistant enrichment |
| Sigma | Optional research / prototyping asset |
| n8n | Optional / transitional / experimental orchestration asset |

---

## First-use flow

```mermaid
flowchart LR
    A[Wazuh or reviewed source family] --> B[Substrate Detection Record]
    B --> C[AegisOps Analytic Signal Admission]
    C --> D[Alert Queue]
    D --> E[Case and Evidence]
    E --> F[Cited Recommendation]
    F --> G[Action Request]
    G --> H[Human Approval]
    H --> I{Approved?}
    I -->|No / Expired / Rejected| J[Record outcome and keep review state explicit]
    I -->|Yes| K[Reviewed Delegation]
    K --> L[Shuffle or reviewed executor]
    L --> M[Action Execution]
    M --> N[Reconciliation]
    N --> O[Operator-visible audit trail]
```

### Assistant path

The assistant is downstream of reviewed records and remains advisory-only.

```mermaid
flowchart TD
    A[Alert / Case / Evidence / Recommendation / Reconciliation] --> B[Reviewed grounding snapshot]
    B --> C[Safe Query Gateway when bounded lookup is needed]
    C --> D[Cited advisory output]
    D --> E[Operator review]
    E --> F[AI Trace / Recommendation review records]
```

Important:

- the assistant does **not** approve actions
- the assistant does **not** execute actions
- the assistant does **not** become reconciliation truth
- optional OpenSearch enrichment is secondary and must never outrank reviewed control-plane truth

---

## Current status

As of the current mainline phase, AegisOps is no longer just a design repo.

It already has:

- a bootable control-plane runtime
- reviewed Wazuh-backed live ingest
- thin operator surfaces for queue / alert / case / cited advisory review
- a first live low-risk action path: `notify_identity_owner`
- reviewed Shuffle delegation for that path
- authoritative `Action Execution` and `Reconciliation`
- production-like auth / secret-loading / readiness / restore / observability hardening
- a reviewed second identity-rich live source onboarding path

It is still **not**:

- a broad autonomous response platform
- a broad multi-action automation catalog
- a broad source-breadth SIEM
- a high-risk live action platform
- a 24x7 SOC product

---

## The first reviewed live action

The first reviewed live action is intentionally narrow:

- **Action:** `notify_identity_owner`
- **Class:** `Notify`
- **Execution path:** reviewed Shuffle delegation
- **Safety model:** approval-bound when required, exact binding preserved, authoritative `Action Execution` and `Reconciliation` retained by AegisOps

This is deliberate.

AegisOps grows by widening **reviewed, fail-closed paths** one at a time, not by opening a broad automation catalog early.

---

## Core principles

- **Detection, control, automation, and execution are explicitly separated**
- **AegisOps owns policy-sensitive workflow truth**
- **Approval and execution are separate first-class records**
- **Evidence and AI output are not the same thing**
- **Fail closed is the default**
- **Reverse-proxy-only ingress is the reviewed path**
- **Secrets are never committed to Git**
- **Restore, readiness, and observability are product requirements, not afterthoughts**
- **AI remains advisory-only**

---

## What an operator can do today

Within the current reviewed live slice, an operator can:

- inspect the analyst queue
- review alert details
- review case details
- inspect evidence provenance and reviewed context
- review cited advisory output
- create a reviewed action request from a cited recommendation
- send the first reviewed live low-risk action (`notify_identity_owner`) through the approved path
- inspect authoritative execution and reconciliation state
- use backup / restore / readiness / health surfaces within the reviewed runtime boundary

---

## What is intentionally still narrow

The following areas remain intentionally narrow or deferred:

- broader live action catalog beyond the first low-risk path
- high-risk executor wiring in production-like mainline
- broad source expansion beyond reviewed identity-rich families
- broad browser-first UI expansion
- AI authority of any kind over approval / execution / reconciliation
- OpenSearch as a required mainline dependency
- n8n as the mainline security orchestration path

---

## Repository layout

```text
aegisops/
├── docs/
├── control-plane/
├── postgres/
├── proxy/
├── ingest/
├── opensearch/   # optional / transitional
├── sigma/        # optional / transitional
├── n8n/          # optional / transitional
├── scripts/
├── config/
└── .env.sample
```

Notes:

- `control-plane/` is the home of the live AegisOps runtime
- `postgres/control-plane/` is the home of the reviewed control-plane schema and migrations
- `opensearch/`, `sigma/`, and `n8n/` remain tracked, but they are not the product core

---

## Safety model at a glance

### Action classes

| Class | Meaning | Mainline posture |
| --- | --- | --- |
| `Read` | Non-mutating lookup or inspection | Allowed within reviewed boundaries |
| `Notify` | Communication without changing the protected target | First live mainline path exists |
| `Soft Write` | Reversible low-impact external coordination or workflow state change | Future narrow expansion only |
| `Hard Write` | Material target-state change | Not a broad live mainline capability |

### Approval model

- requester, approver, and executor identities remain distinct
- approval binds exact request scope and payload
- downstream observed execution must preserve reviewed binding identifiers
- reconciliation mismatches are preserved explicitly

---

## Source strategy

AegisOps prefers **identity-rich** source families before broad generic expansion.

Current reviewed direction:

- Wazuh as the first live detection substrate
- GitHub audit as an important reviewed live slice
- identity-rich second source onboarding already started
- next source growth remains narrow and reviewed

The goal is not to ingest everything.
The goal is to ingest source families that preserve accountable actor, target, privilege, and provenance context.

---

## AI / assistant strategy

The assistant is useful only when it stays inside the reviewed boundary.

It must:

- ground on reviewed control-plane records first
- preserve citations for every claim
- fail closed on identity ambiguity when stable identifiers differ
- treat prompt text as untrusted input
- fall back to control-plane-only grounding when optional enrichment is absent or conflicting

It must not:

- approve actions
- execute actions
- mutate authoritative records as final authority
- turn optional OpenSearch enrichment into authoritative truth

---

## Non-goals

The following are intentionally not current goals:

- full autonomous response
- unrestricted destructive automation
- high-risk action broadening
- commercial-SIEM-style source breadth
- multi-tenant platform design
- premature enterprise control-plane expansion
- AI-first SOC operation

---

## Who should use AegisOps

AegisOps is best suited for:

- small SecOps teams
- business-hours operator workflows
- environments that want reviewed, fail-closed automation growth
- teams that care more about evidence, approval, and reconciliation quality than about broad automation quantity

It is **not** trying to be the fastest way to enable every automation everywhere.
It is trying to be a safer way to operate a narrow but trustworthy SecOps control plane.

---

## Where to look next

Recommended starting points for a new reader:

- `docs/requirements-baseline.md`
- `docs/control-plane-state-model.md`
- `docs/automation-substrate-contract.md`
- `docs/response-action-safety-model.md`
- `docs/phase-15-identity-grounded-analyst-assistant-boundary.md`
- `docs/runbook.md`

If you want the shortest mental model, remember this:

> **Wazuh detects. AegisOps decides, records, and reconciles. Shuffle executes only the reviewed delegated work.**

