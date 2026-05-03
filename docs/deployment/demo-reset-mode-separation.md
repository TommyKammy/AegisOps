# Phase 55.4 Demo Reset and Mode Separation

- **Status**: Accepted as Phase 55.4 demo reset and mode separation contract
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/deployment/demo-seed-contract.md`, `docs/getting-started/first-user-journey.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1175, #1178, #1179

This contract defines repeatable demo reset behavior and demo/live mode separation for the Phase 55 guided first-user journey only.

It does not implement production reset, backup, restore, support bundle behavior, supportability cleanup, report export, daily SOC workbench behavior, Beta readiness, RC readiness, GA readiness, or commercial readiness.

## 1. Purpose

Phase 55.4 gives first-user demos one bounded reset contract so the same demo can be repeated without deleting, relabeling, mutating, or closing live records.

Demo reset targets only records that are explicitly labeled with `demo-only`, `first-user-rehearsal`, and `not-production-truth` and bound to the reviewed demo fixture bundle.

Live records, production records, audit records, unlabeled records, imported customer records, and non-demo workflow truth must remain unchanged after every demo reset attempt.

## 2. Demo Reset Contract

| Reset boundary | Required behavior | Rejection rule |
| --- | --- | --- |
| Selector scope | Reset must use a structured selector for bundle `phase-52-7-demo-seed` and all three required demo labels. | Selectors based on profile name, timestamp, path shape, title, nearby metadata, inferred parent lineage, or partial labels fail. |
| Repeatability | Reset must upsert or replace the same demo family by stable demo identifiers. | Appending duplicate authoritative records, changing stable identifiers, or widening the target set fails. |
| Live preservation | Reset must preserve live, production, audit, imported, customer-private, unlabeled, and non-demo workflow records byte-for-byte. | Any deleted live record, changed production-truth field, audit mutation, or customer-data cleanup fails. |
| Failure cleanup | Rejected reset attempts must leave durable live and non-demo state unchanged. | Any partial durable write, orphan record, half-reset state, or untracked cleanup result fails. |

Demo reset must be repeatable by stable demo identifiers and must not append duplicate authoritative records.

A failed or rejected demo reset must leave durable live and non-demo state unchanged.

## 3. Mode Separation

| Mode | Authority posture | Reset rule |
| --- | --- | --- |
| Demo | Explicit rehearsal mode for records labeled `demo-only`, `first-user-rehearsal`, and `not-production-truth` with `authority=demo_rehearsal_only`. | Demo reset may replace only the reviewed demo bundle by stable demo identifiers and must keep demo badges visible. |
| Live | Authoritative workflow mode for AegisOps control-plane records, production truth, audit truth, and customer-bound records. | Demo reset cannot delete, mutate, relabel, close, reconcile, approve, or clean live records. |

Demo mode is explicit rehearsal mode. Live mode is authoritative workflow mode.

Reset output, UI state, browser state, logs, verifier output, issue-lint output, and demo labels cannot override authoritative AegisOps live records or production truth.

## 4. Reset Safety Rules

Demo reset validation must fail closed when:

- a reset selector omits any required demo label;
- a reset selector targets unlabeled, live, production, imported, audit, customer-private, or non-demo workflow records;
- a reset attempts to close, reconcile, approve, relabel, or mutate production truth;
- a reset uses UI state, browser state, logs, issue-lint output, verifier output, demo output, or fixture text as authority for live records;
- a reset relies on naming convention, path shape, timestamp, comments, adjacent metadata, profile name alone, or inferred lineage to decide scope; or
- a reset is presented as backup, restore, supportability cleanup, production cleanup, support bundle, or disaster-recovery behavior.

Reset reported as backup/restore supportability must fail because this slice does not implement backup, restore, support bundle, or production cleanup behavior.

## 5. Fixture Expectations

Fixture expectations live under `docs/deployment/fixtures/demo-reset-mode-separation/`.

| Fixture | Expected validity | Required rejection |
| --- | --- | --- |
| `valid-repeatable-demo-reset.json` | `valid` | None |
| `delete-live-record.json` | `invalid` | demo reset deletes live records |
| `mutate-production-truth.json` | `invalid` | demo reset mutates production truth |
| `unlabeled-record-reset.json` | `invalid` | demo reset targets unlabeled records |
| `backup-restore-claim.json` | `invalid` | reset reported as backup/restore supportability |

Negative fixtures must fail closed when demo reset deletes live records, mutates production truth, targets unlabeled records, or is reported as backup/restore supportability.

## 6. Validation Rules

Validation must fail closed when:

- this contract is missing;
- reset boundary rows are missing or incomplete;
- mode separation rows are missing or incomplete;
- fixture expectations are missing;
- a negative fixture becomes valid;
- a valid fixture deletes or mutates live records;
- a valid fixture appends duplicate demo records instead of repeating stable demo identifiers;
- reset output is presented as backup, restore, supportability, production cleanup, production truth, gate truth, approval truth, execution truth, reconciliation truth, or closeout truth; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<runtime-env-file>`, `<profile-name>`, `<supervisor-config-path>`, and `<codex-supervisor-root>`.

## 7. Forbidden Claims

- Demo reset may delete live records.
- Demo reset may mutate production truth.
- Unlabeled records may be reset.
- Demo reset is backup restore supportability.
- Demo reset is production cleanup.
- Demo mode is live mode.
- Live records are demo records.
- Demo labels override production truth.

## 8. Validation

Run `bash scripts/verify-phase-55-4-demo-reset-mode-separation.sh`.

Run `bash scripts/test-verify-phase-55-4-demo-reset-mode-separation.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1179 --config <supervisor-config-path>`.

The verifier must fail when the contract is missing, reset or mode-separation rows are incomplete, demo reset deletes live records, demo reset mutates production truth, an unlabeled record is reset, reset is reported as backup/restore supportability, README does not link this contract, or publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No production reset or destructive cleanup is implemented here.
- No backup, restore, support bundle, supportability cleanup, or disaster-recovery behavior is implemented here.
- No report export implementation is approved here.
- No daily SOC workbench, SIEM breadth, SOAR breadth, Beta, RC, GA, or commercial-readiness claim is approved here.
- No demo record, demo label, reset output, UI state, browser state, log text, verifier output, or issue-lint output becomes production truth, gate truth, approval truth, execution truth, reconciliation truth, closeout truth, or authoritative workflow truth.
