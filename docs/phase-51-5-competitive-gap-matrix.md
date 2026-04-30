# Phase 51.5 Competitive Gap Matrix

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0011-phase-51-1-replacement-boundary.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-51-4-smb-personas-jobs-to-be-done.md`
- **Related Issues**: #1041, #1042, #1046

This matrix is competitive and product-planning documentation only. It does not implement SIEM, SOAR, Wazuh, Shuffle, AI, admin, packaging, supportability, installer, operator UI, report export, restore, upgrade, or release-gate behavior.

## 1. Purpose

Phase 51.5 records the competitive gap view for the post-Phase50 SMB replacement roadmap.

The replacement target is an operating experience above Wazuh and Shuffle. It is not a promise that AegisOps will rebuild every detector, every automation integration, every enterprise SIEM/SOAR feature, or every human approval decision.

This document compares AegisOps against four practical alternatives an SMB buyer or operator may use today:

- standalone Wazuh operations,
- standalone Shuffle operations,
- manual SOC or ticket workflow,
- common SMB SIEM/SOAR expectations.

The purpose is to keep later roadmap work honest about current gaps while preserving the authority boundary from the Phase 51 replacement ADR and the Pilot, Beta, RC, and GA gate contract.

## 2. Authority Boundary

AegisOps owns reviewed operating truth for admitted alerts, cases, evidence, recommendations, approvals, action requests, execution receipts, reconciliation, audit, release gates, and known limitations.

AegisOps does not replace every Wazuh detector, every Shuffle integration, every manual approval decision, or every enterprise SIEM/SOAR capability.

Wazuh remains the detection substrate. Shuffle remains the routine automation substrate. Tickets, reports, support notes, dashboards, exports, and AI remain subordinate or derived context unless a later reviewed implementation explicitly binds their evidence to authoritative AegisOps records.

## 3. Competitive Gap Matrix

| Comparison target | What that alternative does well today | AegisOps current state | Beta target | RC target | GA target | Priority | Later phase mapping |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Standalone Wazuh operations | Broad detector ecosystem, endpoint and log signal collection, Wazuh-native alert visibility, and familiar security telemetry primitives. | AegisOps already treats Wazuh as subordinate signal evidence, but the replacement operating experience still lacks the completed SMB Wazuh intake profile and operator-facing admission evidence for the Phase 52-67 roadmap. | Reviewed Wazuh-backed SMB signal admission is repeatable enough for expanded operator validation. | Wazuh signal evidence is part of the complete RC gate packet without moving alert, case, or release truth into Wazuh. | Real-user or design-partner evidence proves Wazuh signal admission works across the intended launch scope. | P0 | Phase 54 Wazuh signal intake, Phase 55 daily operator queue, Phase 66 RC evidence packet, Phase 67 GA launch evidence. |
| Standalone Shuffle operations | Flexible workflow execution, integration breadth, and quick automation composition after an operator defines the process. | AegisOps has reviewed delegation foundations, but the replacement target still needs end-to-end approval ergonomics, delegated execution evidence, mismatch handling, and reconciliation closure for the SMB operating path. | Delegated Shuffle execution can be reviewed with explicit approval, execution receipt, and reconciliation linkage. | Shuffle evidence is part of the RC packet only as subordinate delegated execution evidence. | Launch evidence proves routine delegated execution works without making workflow success authoritative by itself. | P0 | Phase 56 approval ergonomics, Phase 59 delegated execution, Phase 60 reconciliation, Phase 66 RC evidence packet, Phase 67 GA launch evidence. |
| Manual SOC/ticket workflow | Human flexibility, familiar handoffs, ad hoc escalation, and lightweight coordination through existing ticket queues or chat. | AegisOps improves record-chain discipline, but current state does not yet prove the daily replacement queue, handoff ergonomics, report export, support bundle, or limitation-owner workflow for part-time SMB operators. | Daily queue and handoff evidence can replace the brittle manual handoff for design-partner operators. | RC evidence includes report, support, limitation, approval, and reconciliation packets tied to authoritative AegisOps records. | GA evidence proves the operating experience works without treating tickets, chat, support notes, or exports as workflow truth. | P0 | Phase 55 daily operator queue, Phase 62 report export, Phase 63 support bundle, Phase 64 limitation ownership, Phase 66 RC evidence packet, Phase 67 GA launch evidence. |
| Common SMB SIEM/SOAR expectations | Buyers expect guided setup, a usable triage queue, understandable reporting, basic admin and secret custody, restore and upgrade evidence, supportability, and known limitation ownership. | AegisOps is pre-GA and not yet a self-service commercial replacement. The current foundation must still close setup, install, admin custody, AI trace, restore, report, support, upgrade, RC, and GA evidence gaps. | Beta proves repeatable setup and operator evidence for expanded validation while keeping known gaps explicit. | RC proves the intended SMB operating scope through complete evidence packets and accepted limitation owners. | GA requires real-user or design-partner evidence for the intended launch scope plus support-readiness and limitation ownership. | P0/P1 | Phase 52 setup and guided onboarding, Phase 53 install profile, Phase 57 AI advisory trace, Phase 58 admin and secret custody, Phase 61 restore dry-run, Phase 62 report export, Phase 63 support bundle, Phase 64 limitation ownership, Phase 65 upgrade plan, Phase 66 RC evidence packet, Phase 67 GA launch evidence. |

## 4. P0 and P1 Gap Closure Map

| Priority | Gap | Why it is still open | Closure phase or disposition |
| --- | --- | --- | --- |
| P0 | Guided setup and deployment path | Current state is not a self-service replacement because install, profile selection, and first-use onboarding still need a reviewed guided path. | Phase 52 setup and guided onboarding, Phase 53 install profile |
| P0 | Wazuh signal admission from replacement profile | Current state does not yet prove the replacement operating experience for Wazuh-backed SMB signal intake across the intended profile. | Phase 54 Wazuh signal intake |
| P0 | Daily operator queue and handoff ergonomics | Current state does not yet prove the daily replacement workflow for part-time SMB operators. | Phase 55 daily operator queue |
| P0 | Approval, delegated execution, and reconciliation operating path | Current state has reviewed foundations, but the replacement target still needs end-to-end approval ergonomics, Shuffle delegation evidence, and reconciliation closure. | Phase 56 approval ergonomics, Phase 59 delegated execution, Phase 60 reconciliation |
| P0 | Restore, support, limitations, RC, and GA evidence chain | Current state cannot claim replacement readiness until restore, support bundle, known limitation ownership, RC evidence, and GA evidence are complete. | Phase 61 restore dry-run, Phase 63 support bundle, Phase 64 limitation ownership, Phase 66 RC evidence packet, Phase 67 GA launch evidence |
| P1 | Advisory AI trace, reporting, admin custody, and upgrade plan | Current state does not yet provide the replacement-grade advisory trace, leadership reporting, admin secret custody, or upgrade evidence expected by SMB buyers. | Phase 57 AI advisory trace, Phase 58 admin and secret custody, Phase 62 report export, Phase 65 upgrade plan |
| P1 | Enterprise SIEM/SOAR parity | Deferred: broad enterprise SIEM/SOAR parity, broad source coverage, 24x7 SOC services, HA/multi-tenant enterprise operations, and every vendor integration remain outside the Phase 52-67 SMB replacement target unless a later roadmap explicitly accepts them. | Explicitly deferred beyond Phase 67 |

## 5. Target-State Boundaries

AegisOps current state is pre-GA and must not be described as already closing Beta, RC, or GA gaps.

Beta target gaps must remain explicitly open until later phases produce evidence.

RC target gaps must remain explicitly open until Phase 66 evidence exists.

GA target gaps must remain explicitly open until Phase 67 real-user or design-partner evidence exists.

The matrix allows later issues to prioritize product gaps, but it does not approve new authority paths. Later phases must still prove the behavior at the real enforcement boundary and keep Wazuh, Shuffle, tickets, reports, support notes, dashboards, exports, and AI subordinate to AegisOps-owned records.

## 6. Validation

Run `bash scripts/verify-phase-51-5-competitive-gap-matrix.sh`.

Run `bash scripts/test-verify-phase-51-5-competitive-gap-matrix.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1046 --config <supervisor-config-path>`.

The verifier must fail when the Wazuh comparison or Shuffle comparison is missing, when manual SOC/ticket workflow or common SMB SIEM/SOAR expectations are omitted, when a P0/P1 gap lacks a later phase or explicit deferral, when the matrix claims full enterprise SIEM/SOAR parity, when it claims AegisOps already closes future Beta, RC, or GA gaps, or when Wazuh, Shuffle, tickets, or AI are promoted into authority.

## 7. Non-Goals

- No SIEM, SOAR, Wazuh, Shuffle, AI, admin, packaging, supportability, installer, operator UI, report export, restore, upgrade, release-gate, detector, workflow, ticketing, or runtime behavior changes.
- No claim that AegisOps is already GA, already self-service commercial, or already closing later Beta, RC, or GA gaps.
- No claim that AegisOps replaces all Wazuh detection content, all Shuffle integrations, all enterprise SIEM/SOAR capability, all manual approval decisions, or customer accountability for security operations.
- No Wazuh, Shuffle, ticket, support-note, report, dashboard, export, or AI output becomes authoritative for AegisOps records.
