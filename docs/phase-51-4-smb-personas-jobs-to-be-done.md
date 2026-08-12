# Phase 51.4 SMB Personas and Jobs-to-Be-Done Matrix

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0011-phase-51-1-replacement-boundary.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/smb-footprint-and-deployment-profile-baseline.md`
- **Related Issues**: #1041, #1042, #1045

This document defines product-planning personas and jobs-to-be-done for the post-Phase50 SMB replacement roadmap.

This document changes documentation and verification only. It does not implement RBAC, UI, support, AI, admin, Wazuh, Shuffle, ticketing, or evidence-system behavior.

## 1. Purpose

The Phase 51 replacement roadmap needs concrete SMB users so setup, operator UI, administration, supportability, reporting, AI advisory, and release-gate work can target real jobs without widening authority.

These personas describe who the later roadmap serves, what each person needs to get done during normal business-hours security work, what each person is anxious about, where handoffs break down, and which authority limits must remain explicit.

The matrix is planning input only. Runtime roles, permissions, workflow implementation, support access, AI behavior, and admin behavior still require separately reviewed implementation work.

## 2. Shared Operating Assumptions

The default staffing model is business-hours security work with explicit after-hours escalation, not a 24x7 staffed SOC.

The target customer is a single-company or single-business-unit SMB deployment where a small team splits security operations across IT, part-time security work, named approvers, and platform administration.

AegisOps replaces the daily SMB SecOps operating experience above Wazuh and Shuffle. It does not replace Wazuh internals, Shuffle internals, every SIEM/SOAR capability, or customer accountability for approval and escalation decisions.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, and limitation truth.

External support collaborators, AI, Wazuh, Shuffle, tickets, evidence systems, dashboards, report exports, and operator-facing summaries remain subordinate context.

## 3. Personas and Jobs-to-Be-Done Matrix

| Persona | Primary job-to-be-done | Daily jobs | Anxieties | Handoff needs | Authority limits | Later roadmap phases |
| --- | --- | --- | --- | --- | --- | --- |
| Internal IT Manager | Keep daily security work understandable while also owning normal IT operations. | Review prioritized alerts, confirm business impact, decide which issues need operator follow-up, coordinate with approvers, and keep leadership aware of limitations. | Fear that AegisOps becomes another broad SIEM/SOAR program, requires 24x7 staffing, hides risky automation behind AI, or leaves unclear ownership after a failed action. | Needs concise business-hours queue summaries, clear evidence links, explicit escalation owner handoff, and release-gate or limitation summaries that can be shared internally. | May request investigation, update non-approval case context, and coordinate follow-up within assigned scope. Must not approve their own approval-sensitive requests, use IT ownership as platform-admin authority, or treat Wazuh, Shuffle, AI, tickets, or support advice as authoritative AegisOps truth. | Phase 52 setup and guided onboarding, Phase 55 daily operator queue, Phase 62 report export, Phase 66 RC evidence packet, Phase 67 GA launch evidence. |
| Part-Time Security Operator | Triage real signals efficiently without becoming a full-time SOC analyst. | Review admitted Wazuh signals, group related evidence, create or update AegisOps cases, draft action requests, check delegated Shuffle receipts, and prepare handoff notes before returning to other work. | Fear missing critical context, being blamed for automation they did not approve, losing the thread across shifts, or having AI produce confident but unaudited guidance. | Needs saved investigation state, next-step prompts, evidence anchors, explicit approval status, failed-delegation cleanup notes, and handoff text that a later operator can resume. | May investigate, annotate, and request approval-bound actions within assigned scope. Must not self-approve sensitive actions, execute destructive actions outside reviewed delegation, close cases from AI advice alone, or promote raw Wazuh or Shuffle state into AegisOps reconciliation truth. | Phase 54 Wazuh signal intake, Phase 55 daily queue, Phase 57 AI advisory trace, Phase 59 Shuffle delegated execution, Phase 61 restore dry-run evidence. |
| Approver / Escalation Owner | Make accountable decisions on actions that need human authority or after-hours escalation. | Review requester identity, evidence, risk, blast radius, proposed action, rollback owner, and timing; approve or reject within delegated authority; decide when after-hours escalation is justified. | Fear rubber-stamp approvals, unclear separation from the requester, missing rollback context, or hidden support or AI pressure to approve an unsafe action. | Needs immutable approval context, requester separation, explicit action intent, rollback and mismatch handling notes, and after-hours escalation reason captured in the AegisOps record. | May approve or reject approval-bound requests within delegated scope and own escalation decisions. Must remain distinct from the requester where required, must not rely on side-channel approvals alone, and must not let support, AI, tickets, Wazuh, or Shuffle approve actions by proxy. | Phase 56 approval ergonomics, Phase 59 delegated execution, Phase 60 reconciliation, Phase 64 limitation ownership, Phase 66 RC evidence packet. |
| Platform Admin | Keep AegisOps deployable, recoverable, connected, and auditable for the SMB footprint. | Configure reviewed runtime settings, maintain identity and secret boundaries, run install or upgrade preflights, collect support bundles, rehearse restore and rollback, and repair platform connectivity without changing case truth. | Fear brittle installs, hidden credential drift, backup or restore gaps, unclear ownership of service accounts, or being asked to bypass approvals during an incident. | Needs deterministic preflight output, repo-relative runbooks, secret-custody checks, backup and restore manifests, support-bundle redaction guidance, and clear separation from approver authority. | May administer platform components, service-account plumbing, recovery procedures, and approved configuration paths. Must not use platform-admin access as a substitute approval path, mutate authoritative case or reconciliation outcomes outside reviewed controls, or grant external support direct backend or substrate authority. | Phase 52 setup, Phase 53 install profile, Phase 58 admin and secret custody, Phase 61 restore dry-run, Phase 63 support bundle, Phase 65 upgrade plan. |
| Bounded External Support Collaborator | Help diagnose platform or product issues without becoming an operator, approver, administrator, or source of truth. | Review redacted support bundles, ask clarifying questions, suggest documented remediation steps, and identify product defects or known limitations for the customer-owned team to accept or reject. | Fear receiving private production data, being expected to provide 24x7 coverage, being blamed for customer decisions, or accidentally becoming an authority path through informal advice. | Needs redacted bundles, explicit customer owner, limitation owner, reproduction steps, environment class, retained evidence references, and a written boundary for what support may not do. | May provide advisory diagnosis from redacted evidence and documented product knowledge only. Must not access customer-private production systems directly, approve actions, execute actions, mutate AegisOps records, operate Wazuh or Shuffle, close cases, or make AI, tickets, or support notes authoritative. | Phase 63 support bundle, Phase 64 known limitations ownership, Phase 66 RC supportability evidence, Phase 67 GA support-readiness evidence. |

### 3.1 Internal IT Manager

The internal IT manager is often the person accountable for keeping the security program understandable to the business. This persona needs AegisOps to compress security work into clear queues, explicit escalation choices, and evidence-backed status without asking the IT manager to become a full-time analyst or platform administrator.

### 3.2 Part-Time Security Operator

The part-time security operator performs real triage in bounded windows. This persona needs durable state, clear next actions, and handoff notes because the same operator may leave the queue for ordinary IT work and return later.

### 3.3 Approver / Escalation Owner

The approver or escalation owner carries the accountable decision. This persona needs complete context, requester separation, and a recorded decision path so approval-sensitive work does not collapse into chat, support advice, AI output, or automation success.

### 3.4 Platform Admin

The platform admin keeps AegisOps installed, configured, backed up, upgraded, and recoverable. This persona can operate infrastructure but does not gain approval authority or case-truth authority by administering the platform.

### 3.5 Bounded External Support Collaborator

The bounded external support collaborator helps from redacted, customer-approved evidence. This persona is intentionally not an operator, approver, administrator, substrate owner, or authoritative record owner.

## 4. Later Roadmap Usage

| Persona | Primary later phases | Usage |
| --- | --- | --- |
| Internal IT Manager | Phase 52, Phase 55, Phase 62, Phase 66, Phase 67 | Shapes setup language, daily summaries, leadership-ready reports, RC evidence, and GA launch evidence around narrow SMB ownership. |
| Part-Time Security Operator | Phase 54, Phase 55, Phase 57, Phase 59, Phase 61 | Shapes signal triage, queue ergonomics, advisory AI traces, delegated execution review, and restore-readiness handoffs. |
| Approver / Escalation Owner | Phase 56, Phase 59, Phase 60, Phase 64, Phase 66 | Shapes approval context, separation-of-duties proof, reconciliation ownership, limitations decisions, and RC gate packets. |
| Platform Admin | Phase 52, Phase 53, Phase 58, Phase 61, Phase 63, Phase 65 | Shapes install, configuration, secret custody, restore rehearsal, support-bundle, and upgrade-plan requirements. |
| Bounded External Support Collaborator | Phase 63, Phase 64, Phase 66, Phase 67 | Shapes redacted support-bundle evidence, limitation ownership, supportability proof, and GA support-readiness boundaries. |

Later roadmap issues may cite this matrix when defining user-facing setup, operator queue, approval, admin, support, AI advisory, reporting, release-gate, and launch-readiness work.

## 5. Authority Boundary

These personas do not grant external support, AI, Wazuh, Shuffle, tickets, evidence systems, dashboards, reports, or operator-facing summaries authority over AegisOps records.

Support collaborators provide advisory diagnosis only from redacted evidence and documented product knowledge. Customer-owned AegisOps operators, approvers, and platform administrators remain responsible for admitting evidence, approving actions, changing platform state, and recording durable outcomes.

AI remains advisory-only and must stay attached to reviewed recommendation, evidence, and human decision records. AI output must not approve, execute, reconcile, close, activate, administer, or define source truth.

Wazuh remains the detection substrate. Shuffle remains the routine automation substrate. Their outputs become AegisOps workflow evidence only through reviewed admission, approval, execution receipt, and reconciliation records.

## 6. Validation

Run `bash scripts/verify-phase-51-4-smb-personas-jtbd.sh`.

Run `bash scripts/test-verify-phase-51-4-smb-personas-jtbd.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1045 --config <supervisor-config-path>`.

The verifier must fail when the bounded external support collaborator is missing, when persona text grants external support or AI authority over AegisOps records, or when the document assumes 24x7 SOC staffing as the default.

## 7. Non-Goals

- No RBAC implementation, permission assignment, UI implementation, support workflow, AI workflow, admin workflow, Wazuh behavior, Shuffle behavior, ticketing behavior, or evidence-system behavior changes.
- No support collaborator receives direct customer-private production access, backend access, approval authority, execution authority, substrate authority, or authority over AegisOps records.
- No AI, ticket, Wazuh, Shuffle, support note, report, dashboard, export, or operator-facing summary becomes authoritative workflow truth.
- No 24x7 staffed SOC promise, formal SLA, self-service GA claim, or broad SIEM/SOAR replacement claim is created by this matrix.
