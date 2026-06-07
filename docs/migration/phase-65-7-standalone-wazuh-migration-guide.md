# Phase 65.7 Standalone Wazuh Migration Guide

- **Status**: Accepted as Phase 65 beta/design-partner migration guidance only.
- **Date**: 2026-06-07
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1381
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-51-5-competitive-gap-matrix.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/deployment/wazuh-manager-intake-binding-contract.md`, `docs/deployment/wazuh-source-health-projection-contract.md`, `docs/deployment/wazuh-authority-boundary-negative-tests.md`

This guide helps a beta/design-partner operator plan a migration from standalone Wazuh operations into the bounded Phase 65 AegisOps packaging posture.

The guide is documentation and planning evidence only. It does not implement automated migration tooling, production customer-data import, Wazuh detector expansion, source-native truth promotion, broad SIEM parity, RC proof, GA proof, or commercial replacement readiness.

## 1. Prerequisites

- A reviewed Phase 65.1 release bundle inventory reference for the candidate AegisOps package.
- A Wazuh manager, indexer, dashboard, and agent scope that can be described without embedding secrets, customer-private data, raw alert payloads, or workstation-local absolute paths.
- A reviewed source onboarding owner who can map Wazuh signal families into AegisOps source-family and admission terminology.
- Existing Wazuh rule, decoder, alert, and dashboard references retained as subordinate context only.
- A Phase 51.3 gate boundary owner who can confirm that Wazuh status cannot satisfy Beta, RC, or GA gates by itself.

## 2. Non-Goals

- No automated Wazuh migration command, Wazuh configuration generator, Wazuh upgrader, Wazuh certificate generator, or fleet-management feature is added.
- No production customer-data import, raw alert import, unredacted log import, or arbitrary source-native record import is approved.
- No new Wazuh detector breadth, broad SIEM parity, release-candidate behavior, general-availability behavior, production support readiness, or commercial replacement readiness is claimed.
- No Wazuh manager, indexer, dashboard, alert, rule, decoder, source-health projection, or agent state becomes authoritative AegisOps truth.

## 3. Authority Boundary

Standalone Wazuh remains the detection substrate. Wazuh may contribute subordinate signal evidence after reviewed AegisOps admission and linkage, but AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, workflow, and closeout truth.

Operators must preserve the distinction between Wazuh-native observability and AegisOps-owned record truth. Wazuh alert identifiers, dashboard states, rule states, indexer status, manager status, agent status, generated configuration, source-health projection, verifier output, issue-lint output, support notes, screenshots, and operator summaries are planning context until a reviewed AegisOps record binds them explicitly.

## 4. Evidence Mapping

| Standalone Wazuh artifact | AegisOps migration target | Required handling |
| --- | --- | --- |
| Wazuh manager and indexer version notes | Profile inventory context | Record versions as subordinate compatibility context; do not treat version state as release, gate, or readiness proof. |
| Rule and decoder scope | Source-family onboarding notes | Map reviewed signal families to AegisOps admission expectations; do not bulk-import rules as approved detectors. |
| Raw alerts and event samples | Candidate signal evidence | Redact and reference samples only as candidate evidence; AegisOps admission and linkage decide whether records are created. |
| Dashboard views and saved searches | Operator orientation notes | Preserve as training context; dashboards cannot close cases or prove evidence truth. |
| Agent enrollment posture | Wazuh profile prerequisite notes | Retain enrollment scope and rollback notes using the reviewed Wazuh helper boundary. |
| Source-health observations | Degraded-source review context | Use reviewed source-health projection language; Wazuh availability is not AegisOps workflow truth. |

## 5. Limitation Notes

- Existing standalone Wazuh deployments may contain local rules, decoders, dashboards, or tuning assumptions that are useful context but not reviewed AegisOps detector coverage.
- Any unmapped signal family must remain a named limitation with an owner, follow-up date, and impact note before beta/design-partner handoff.
- Any raw alert or log sample that cannot be redacted must stay outside the Phase 65 package and must not appear in publishable documentation.
- Wazuh-only alert volume, dashboard status, or manager health cannot be used to claim Beta, RC, GA, or commercial replacement readiness.

## 6. Validation Expectations

Before this guide is referenced from a Phase 65 migration handoff, run:

```sh
bash scripts/verify-phase-65-7-migration-guides.sh
bash scripts/test-verify-phase-65-7-migration-guides.sh
bash scripts/verify-phase-51-5-competitive-gap-matrix.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1381 --config <supervisor-config-path>
```

The retained evidence should include the Wazuh scope owner, source-family mapping owner, redaction posture, limitation owners, and the AegisOps record family that would accept any future signal evidence.

## 7. Non-Claims

This migration guide does not claim automated migration, production customer-data import, Wazuh detector parity, broad SIEM parity, Beta gate acceptance, RC readiness, RC gate acceptance, GA readiness, GA gate acceptance, production support readiness, self-service commercial readiness, or commercial replacement readiness.

This migration guide is not workflow authority, release authority, gate authority, source truth, Wazuh truth, verifier truth, issue-lint truth, install truth, support truth, readiness truth, or substitute evidence for the Phase 51.3 gate contract.
