# Phase 55.1 First-User Journey

- **Status**: Accepted as Phase 55.1 operator guidance
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/first-user-stack.md`, `docs/deployment/demo-seed-contract.md`, `docs/phase-52-closeout-evaluation.md`, `docs/phase-53-closeout-evaluation.md`, `docs/phase-54-closeout-evaluation.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1175, #1176

This guide is workflow-first operator guidance for a new AegisOps user. It starts from the Phase 52 few-command stack path and shows the first guided SecOps flow without requiring the full architecture corpus.

It does not implement UI behavior, demo seed records, reset behavior, report export behavior, supportability commands, Phase 56 daily workbench breadth, Phase 58 supportability scope, Phase 62 SOAR breadth, Beta readiness, RC readiness, GA readiness, or commercial readiness.

## 1. Few-Command Entry Path

Run the entry path from a repository checkout with reviewed profile input and documented placeholders. These commands orient the operator before the workflow walkthrough; concrete runtime behavior remains owned by the executable stack issues.

| Step | Command | Operator intent | Expected outcome |
| --- | --- | --- | --- |
| 1 | `aegisops init --profile smb-single-node --runtime-env <runtime-env-file>` | Prepare reviewed local setup placeholders. | Required config placeholders are present, and unsafe or missing prerequisites are surfaced. |
| 2 | `aegisops up --profile smb-single-node --runtime-env <runtime-env-file>` | Start the reviewed first-user stack components available for the profile. | Available components start or report explicit blocked, skipped, or mocked prerequisites. |
| 3 | `aegisops doctor --profile smb-single-node --runtime-env <runtime-env-file>` | Review stack health before workflow rehearsal. | Stack health is summarized as setup evidence, not as workflow truth. |
| 4 | `aegisops seed-demo --profile smb-single-node --demo-mode explicit` | Seed a reviewed demo-only queue for the guided journey. | The queue is labeled demo-only and subordinate to AegisOps control-plane truth. |
| 5 | `aegisops status --profile smb-single-node` | Inspect the local first-user state before opening the operator surface. | Current setup posture and safe next actions are shown without becoming authoritative workflow state. |
| 6 | `aegisops open --profile smb-single-node` | Open or print the reviewed operator access path. | The operator reaches the guided surface; browser state remains subordinate context. |

## 2. Workflow-First Journey

Use the demo-only path to understand the AegisOps flow in this order:

1. **Stack health** - Confirm the reviewed profile is started and the health view shows explicit ready, blocked, skipped, or mocked states.
2. **Seeded queue** - Use `seed-demo` output only as a rehearsal input and verify the queue marks sample records as demo-only.
3. **Sample alert** - Open the sample alert and check source, detection, identity, asset, severity, and ingestion context before escalating.
4. **Case** - Admit the alert into a case only through the AegisOps control-plane case workflow.
5. **Evidence** - Attach or review evidence records that are explicitly bound to the case and alert.
6. **AI summary** - Read the assistant summary as advisory context and compare it with the alert, case, and evidence records before relying on it.
7. **Action review** - Review the proposed action, approval requirement, protected target, expected receipt, and operator decision boundary.
8. **Receipt** - Confirm that any delegated execution returns an execution receipt linked to the approved action request.
9. **Reconciliation** - Compare the execution receipt against the approved request and record the reconciliation outcome before any closeout language.
10. **Report export** - Export or review the report only as a derived artifact from the authoritative alert, case, evidence, action, receipt, and reconciliation records.

## 3. Demo Guidance Versus Production Truth

First-user docs and first-30-minutes guidance are operator guidance only. AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

Demo records, UI state, browser state, Wazuh state, Shuffle state, AI output, tickets, verifier output, and issue-lint output remain subordinate context. Demo-only labels must stay visible, and missing authoritative records must block the journey instead of being inferred from screenshots, downstream status, or sample text.

## 4. Scope Boundaries

This Phase 55.1 slice explains the first-user journey and first 30 minutes only. It keeps the operator focused on the workflow sequence and intentionally avoids deep architecture dumping.

Out of scope here:

- first-login checklist UI implementation;
- demo seed implementation or reset behavior;
- report export implementation;
- supportability commands or break-glass operating procedures;
- daily SOC workbench breadth, SIEM breadth, SOAR breadth, packaging, RC, GA, or commercial launch scope.

## 5. Validation

Run `bash scripts/verify-phase-55-1-first-user-journey-docs.sh`.

Run `bash scripts/test-verify-phase-55-1-first-user-journey-docs.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1176 --config <supervisor-config-path>`.

The focused verifier must fail when the docs are missing, the few-command path is incomplete, the workflow sequence is missing or out of order, demo records are promoted to production truth, publishable docs contain workstation-local absolute paths, or the docs claim Phase 56, Phase 58, Phase 62, Beta, RC, GA, or commercial readiness is complete.
