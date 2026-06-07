# Phase 65.7 Manual SOC And Ticket Workflow Migration Guide

- **Status**: Accepted as Phase 65 beta/design-partner migration guidance only.
- **Date**: 2026-06-07
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1381
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-51-5-competitive-gap-matrix.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/phase-62-5-manual-fallback-contract.md`, `docs/deployment/operator-training-handoff-packet.md`

This guide helps a beta/design-partner operator plan a migration from manual SOC notes, ticket queues, chat handoffs, and spreadsheet-like coordination into the bounded Phase 65 AegisOps packaging posture.

The guide is documentation and planning evidence only. It does not implement automated migration tooling, production customer-data import, ticket-system synchronization, source-native truth promotion, broad SIEM/SOAR parity, RC proof, GA proof, or commercial replacement readiness.

## 1. Prerequisites

- A reviewed Phase 65.1 release bundle inventory reference for the candidate AegisOps package.
- A manual workflow inventory that can be described without embedding secrets, private customer ticket text, raw chat content, raw report exports, or workstation-local absolute paths.
- A daily-operations owner who can map manual triage, escalation, approval, handoff, and reporting steps into AegisOps record families.
- Existing tickets, chat messages, spreadsheets, reports, support notes, and downstream receipts retained as subordinate coordination context only.
- A Phase 51.3 gate boundary owner who can confirm that ticket or chat status cannot satisfy Beta, RC, or GA gates by itself.

## 2. Non-Goals

- No automated ticket import command, chat importer, spreadsheet importer, ticket-system synchronization, or production customer-data import path is added.
- No arbitrary source-native record import, broad SIEM/SOAR parity, release-candidate behavior, general-availability behavior, production support readiness, or commercial replacement readiness is claimed.
- No ticket status, ticket assignment, ticket SLA state, chat decision, spreadsheet row, report export, support note, or downstream receipt becomes authoritative AegisOps truth.
- No manual approval decision is bypassed or treated as reviewed merely because it appeared in an external ticket or chat thread.

## 3. Authority Boundary

Manual SOC and ticket surfaces remain coordination context. They may help operators find historical intent, escalation owners, and evidence pointers, but AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, workflow, and closeout truth.

Operators must preserve the distinction between external coordination state and AegisOps-owned record truth. Ticket status, ticket comments, ticket assignments, ticket SLA fields, chat messages, spreadsheets, report exports, support notes, screenshots, verifier output, issue-lint output, downstream receipts, and operator summaries are planning context until a reviewed AegisOps record binds them explicitly.

## 4. Evidence Mapping

| Manual workflow artifact | AegisOps migration target | Required handling |
| --- | --- | --- |
| Ticket queues and statuses | Case and action-request candidate inventory | Map ticket purpose and owner only; ticket state cannot close cases or prove approval. |
| Chat handoffs and escalation notes | Handoff and limitation-owner context | Retain owner and timing context after redaction; chat text cannot become approval truth. |
| Spreadsheet trackers | Source and case inventory planning | Normalize only identifiers, owners, and candidate relationships; spreadsheet rows are not record truth. |
| Manual approval notes | Approval-policy review input | Recreate approval posture through reviewed AegisOps records before any delegated action is accepted. |
| Report exports | Derived reporting context | Reports must cite authoritative AegisOps records before they can be used in gate evidence. |
| Support notes | Support-bundle planning context | Support notes require redaction and cannot replace gate, release, limitation, or workflow records. |

## 5. Limitation Notes

- Existing manual workflows may contain ambiguous owners, hidden approvals, stale ticket statuses, private customer data requiring redaction, or missing reconciliation evidence that must remain named limitations until reviewed.
- Any manual step that cannot be mapped to an AegisOps record family must remain a named limitation with an owner, follow-up date, and impact note before beta/design-partner handoff.
- Any ticket, chat, spreadsheet, report, or support note content that cannot be redacted must stay outside the Phase 65 package and must not appear in publishable documentation.
- Ticket closure, chat agreement, spreadsheet status, report export, or support note completion cannot be used to claim Beta, RC, GA, or commercial replacement readiness.

## 6. Validation Expectations

Before this guide is referenced from a Phase 65 migration handoff, run:

```sh
bash scripts/verify-phase-65-7-migration-guides.sh
bash scripts/test-verify-phase-65-7-migration-guides.sh
bash scripts/verify-phase-51-5-competitive-gap-matrix.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1381 --config <supervisor-config-path>
```

The retained evidence should include the manual workflow owner, record-family mapping owner, redaction posture, limitation owners, and the AegisOps record family that would accept any future coordination evidence.

## 7. Non-Claims

This migration guide does not claim automated migration, production customer-data import, ticket-system truth, broad SIEM/SOAR parity, Beta gate acceptance, RC readiness, RC gate acceptance, GA readiness, GA gate acceptance, production support readiness, self-service commercial readiness, or commercial replacement readiness.

This migration guide is not workflow authority, release authority, gate authority, source truth, ticket truth, verifier truth, issue-lint truth, approval truth, support truth, readiness truth, or substitute evidence for the Phase 51.3 gate contract.
