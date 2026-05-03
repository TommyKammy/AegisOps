# Phase 55.1 First 30 Minutes

- **Status**: Accepted as Phase 55.1 operator guidance
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Guide**: `docs/getting-started/first-user-journey.md`
- **Related Issues**: #1175, #1176

This guide keeps the first session focused on workflow orientation, not architecture study. It assumes the operator is using the reviewed first-user stack path and wants to understand the AegisOps flow in one short guided pass.

## 1. Minute-by-Minute Path

| Time | Focus | Operator action | Stop condition |
| --- | --- | --- | --- |
| 0-5 minutes | Stack entry | Run the few-command path through `init`, `up`, `doctor`, `seed-demo`, `status`, and `open`. | Stop if stack health is blocked without an explicit safe next action. |
| 5-8 minutes | Demo queue | Confirm the seeded queue is present and marked demo-only. | Stop if demo records are presented without demo-only posture. |
| 8-11 minutes | Alert orientation | Open the sample alert and identify source, detection, asset, identity, severity, and provenance. | Stop if the alert cannot be traced to a control-plane alert record. |
| 11-14 minutes | Case admission | Admit or review the case created from the sample alert. | Stop if case state is inferred from UI text without an authoritative case record. |
| 14-17 minutes | Evidence | Review evidence records linked to the case and alert. | Stop if evidence is only a screenshot, external system status, or unbound note. |
| 17-20 minutes | AI summary | Read the AI summary as advisory context and compare it with the case evidence. | Stop if AI output is treated as approval, evidence, source, case, or closeout truth. |
| 20-23 minutes | Action review | Inspect the proposed action, approval requirement, target, expected receipt, and reviewer decision. | Stop if an action would bypass AegisOps approval or protected-target checks. |
| 23-26 minutes | Receipt | Confirm the execution receipt is linked to the approved action request. | Stop if the receipt is missing, stale, mismatched, or only present in Shuffle, logs, tickets, or browser state. |
| 26-28 minutes | Reconciliation | Review the reconciliation result against the approved action and receipt. | Stop if reconciliation is inferred from downstream success alone. |
| 28-30 minutes | Report export | Review the report export as a derived artifact from authoritative records. | Stop if the export widens scope beyond directly linked alert, case, evidence, action, receipt, and reconciliation records. |

## 2. What To Confirm

The first 30 minutes should leave the operator with a concrete understanding of the AegisOps sequence: stack health, seeded queue, sample alert, case, evidence, AI summary, action review, receipt, reconciliation, and report export.

Use demo-only records only to rehearse the path; they are not production truth. The right outcome is not a production-readiness claim. The right outcome is that the operator can identify which record is authoritative at each step and where the journey must stop when the record is missing.

## 3. Authority Boundary

First-user docs and first-30-minutes guidance are operator guidance only. The authoritative workflow remains the AegisOps control-plane record chain.

Stop and treat the gap as a follow-up if a required control-plane record, receipt, reconciliation result, or export artifact is missing. Do not substitute Wazuh state, Shuffle state, AI output, browser state, UI state, demo records, tickets, logs, verifier output, issue-lint output, or operator-facing status text as workflow truth.

## 4. What This Does Not Prove

This first session does not prove production setup, daily SOC workbench completeness, supportability operations, SOAR breadth, Beta readiness, RC readiness, GA readiness, or commercial readiness.

It also does not implement first-login checklist UI, demo seed records, reset behavior, commercial report breadth, audit export administration, production report templates, runtime setup wizard behavior, supportability commands, or broad daily SOC workflows.

## 5. Validation

Run `bash scripts/verify-phase-55-1-first-user-journey-docs.sh`.

Run `bash scripts/test-verify-phase-55-1-first-user-journey-docs.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1176 --config <supervisor-config-path>`.
