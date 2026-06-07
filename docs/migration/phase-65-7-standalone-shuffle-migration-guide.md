# Phase 65.7 Standalone Shuffle Migration Guide

- **Status**: Accepted as Phase 65 beta/design-partner migration guidance only.
- **Date**: 2026-06-07
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1381
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-51-5-competitive-gap-matrix.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-62-reviewed-automation-catalog-contract.md`, `docs/deployment/shuffle-smb-single-node-profile-contract.md`, `docs/deployment/shuffle-reviewed-workflow-template-contract.md`

This guide helps a beta/design-partner operator plan a migration from standalone Shuffle operations into the bounded Phase 65 AegisOps packaging posture.

The guide is documentation and planning evidence only. It does not implement automated migration tooling, live Shuffle workflow import, production customer-data import, source-native truth promotion, broad SOAR parity, RC proof, GA proof, or commercial replacement readiness.

## 1. Prerequisites

- A reviewed Phase 65.1 release bundle inventory reference for the candidate AegisOps package.
- A standalone Shuffle workflow inventory that can be described without embedding API keys, secrets, private customer payloads, raw execution logs, or workstation-local absolute paths.
- A reviewed automation catalog owner who can map candidate workflows into Read, Notify, or Soft Write action families.
- Existing workflow canvases, app nodes, callbacks, execution receipts, retries, and ticket pointers retained as subordinate context only.
- A Phase 51.3 gate boundary owner who can confirm that Shuffle workflow success cannot satisfy Beta, RC, or GA gates by itself.

## 2. Non-Goals

- No automated Shuffle migration command, live workflow importer, app marketplace expansion, credential importer, or direct ad hoc workflow launcher is added.
- No production customer-data import, arbitrary callback import, raw execution log import, or unreviewed workflow-template import is approved.
- No new Shuffle integration breadth, broad SOAR parity, release-candidate behavior, general-availability behavior, production support readiness, or commercial replacement readiness is claimed.
- No Shuffle frontend, backend, workflow, callback, API, generated config, execution log, retry state, or ticket pointer becomes authoritative AegisOps truth.

## 3. Authority Boundary

Standalone Shuffle remains the routine automation substrate. Shuffle may contribute subordinate delegated-execution evidence only after reviewed AegisOps approval, action intent, execution receipt, and reconciliation linkage. AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, workflow, and closeout truth.

Operators must preserve the distinction between Shuffle workflow activity and AegisOps-owned record truth. Workflow success, workflow failure, callback payloads, execution logs, workflow canvases, app configuration, retry state, ticket pointers, verifier output, issue-lint output, screenshots, support notes, and operator summaries are planning context until a reviewed AegisOps record binds them explicitly.

## 4. Evidence Mapping

| Standalone Shuffle artifact | AegisOps migration target | Required handling |
| --- | --- | --- |
| Workflow inventory | Reviewed automation-catalog candidate list | Map each candidate to Read, Notify, Soft Write, or explicitly out-of-scope; do not import unreviewed templates as approved actions. |
| App and credential usage | Credential custody and support notes | Record required credential classes without values; placeholder or sample credentials are invalid. |
| Callback payload examples | Candidate execution evidence | Redact and reference payload shape only; callback payloads do not become execution receipt truth. |
| Workflow run history | Limitation and rehearsal context | Retain only aggregate or redacted context; workflow success cannot close AegisOps reconciliation. |
| Ticket creation workflows | Ticket-pointer coordination notes | Treat ticket pointers as coordination context; ticket state cannot become case, limitation, release, or gate truth. |
| Manual fallback paths | Manual fallback owner notes | Bind fallback expectations to reviewed AegisOps action requests and owners, not Shuffle status alone. |

## 5. Limitation Notes

- Existing standalone Shuffle deployments may include unreviewed app nodes, direct target mutations, broad connector assumptions, or implicit approvals that are outside Phase 65 migration guidance.
- Any workflow that cannot be mapped to a reviewed catalog action family must remain a named limitation with an owner, follow-up date, and impact note before beta/design-partner handoff.
- Any callback payload, execution log, app credential, or ticket content that cannot be redacted must stay outside the Phase 65 package and must not appear in publishable documentation.
- Shuffle workflow success, ticket creation, or notification delivery cannot be used to claim Beta, RC, GA, or commercial replacement readiness.

## 6. Validation Expectations

Before this guide is referenced from a Phase 65 migration handoff, run:

```sh
bash scripts/verify-phase-65-7-migration-guides.sh
bash scripts/test-verify-phase-65-7-migration-guides.sh
bash scripts/verify-phase-51-5-competitive-gap-matrix.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1381 --config <supervisor-config-path>
```

The retained evidence should include the workflow inventory owner, reviewed catalog mapping owner, redaction posture, limitation owners, and the AegisOps action family that would accept any future delegated-execution evidence.

## 7. Non-Claims

This migration guide does not claim automated migration, production customer-data import, broad Shuffle integration import, broad SOAR parity, Beta gate acceptance, RC readiness, RC gate acceptance, GA readiness, GA gate acceptance, production support readiness, self-service commercial readiness, or commercial replacement readiness.

This migration guide is not workflow authority, release authority, gate authority, source truth, Shuffle truth, verifier truth, issue-lint truth, execution truth, support truth, readiness truth, or substitute evidence for the Phase 51.3 gate contract.
