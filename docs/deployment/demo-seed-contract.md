# Phase 52.7 Demo Seed Contract

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-1-cli-command-contract.md`, `docs/phase-52-2-smb-single-node-profile-model.md`, `docs/deployment/compose-generator-contract.md`, `docs/deployment/env-secrets-certs-contract.md`, `docs/deployment/host-preflight-contract.md`
- **Related Issues**: #1063, #1065, #1070

This contract defines demo seed records and demo/prod separation expectations for the executable first-user stack only. It does not implement the full first-user UI journey, production data import, Wazuh product profiles, Shuffle product profiles, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

The demo seed contract gives later setup and `seed-demo` work one reviewed bundle shape for first-user workflow rehearsal. The bundle may create demo alerts, cases, evidence, action requests, approvals, execution receipts, and reconciliation notes, but every seeded record remains demo-only rehearsal state.

Demo seed output is workflow rehearsal evidence only.

## 2. Authority Boundary

Demo records, demo labels, fixture provenance, reset output, fake secrets, sample credentials, demo source state, and operator-facing seed summaries are not production truth, gate truth, customer evidence, approval truth, execution truth, or reconciliation truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.

## 3. Seed Record Contract

| Record type | Required demo fields | Presentation rule | Production exclusion |
| --- | --- | --- | --- |
| Demo alert | Stable demo alert identifier, fixture provenance, demo source family, demo labels, and reviewed timestamp placeholder. | Must render as demo-only alert rehearsal. | Must not satisfy production alert admission, customer evidence, release gate, or detector activation truth. |
| Demo case | Stable demo case identifier, linked demo alert, analyst owner placeholder, demo labels, and rehearsal status. | Must render as demo-only case rehearsal. | Must not satisfy production case ownership, customer queue state, release gate, or closeout truth. |
| Demo evidence | Stable demo evidence identifier, linked demo case, fixture path, demo labels, and provenance note. | Must render as demo-only evidence rehearsal. | Must not satisfy customer evidence, audit evidence, production detection proof, or release evidence truth. |
| Demo action request | Stable demo action-request identifier, linked demo case, requested action placeholder, demo labels, and non-production scope. | Must render as demo-only action rehearsal. | Must not authorize production action, substrate mutation, approval gate, or execution truth. |
| Demo approval | Explicit demo approval identifier, demo labels, linked demo action request, and reviewer placeholder. | Must render as demo-only approval rehearsal. | Must not satisfy real approval truth, release gate truth, execution authorization, or customer evidence. |
| Demo execution receipt | Stable demo execution receipt identifier, linked demo action request, mocked executor note, and demo labels. | Must render as demo-only execution rehearsal. | Must not satisfy real execution truth, Shuffle truth, substrate mutation proof, or customer evidence. |
| Demo reconciliation note | Stable demo reconciliation identifier, linked demo execution receipt, outcome placeholder, and demo labels. | Must render as demo-only reconciliation rehearsal. | Must not satisfy production reconciliation truth, closeout truth, customer evidence, or release gate truth. |

Every seeded record must include `production_claim=false`, `authority=demo_rehearsal_only`, and an empty `truth_surfaces` list.

## 4. Demo Labels

| Label | Required value | Validation rule |
| --- | --- | --- |
| `demo-only` | Required on every demo seed record. | Missing label fails because the record cannot be separated from production-bound state. |
| `first-user-rehearsal` | Required on every demo seed record. | Missing label fails because the record cannot be bound to the executable first-user rehearsal scope. |
| `not-production-truth` | Required on every demo seed record. | Missing label fails because demo data must never be presented as production truth. |

Rendered operator surfaces must show these labels directly or through an equivalent demo-only badge. Hidden metadata alone is not enough for operator-facing presentation.

## 5. Reset Behavior

| Reset boundary | Required behavior | Rejection rule |
| --- | --- | --- |
| Selector scope | Reset must target only records in the reviewed demo bundle with all required demo labels. | Any selector based on name shape, timestamps alone, profile name alone, or parent lineage inference fails. |
| Production guard | Reset must prove `deletes_production_records=false` and must not touch records outside the demo bundle. | Any reset plan that can delete production, imported, customer-private, or unlabeled records fails. |
| Failure cleanup | Failed seed or reset attempts must leave durable production and non-demo state unchanged. | Any partial write, orphan record, half-reset state, or untracked cleanup result fails. |

Reset output is operator guidance and cleanup evidence for the demo bundle only.

Reset selectors must be structured as `{"bundle":"phase-52-7-demo-seed","labels":["demo-only","first-user-rehearsal","not-production-truth"]}` or an equivalent object with the same bundle and label constraints.

## 6. Production Exclusion Rules

Demo seed validation must reject any record, bundle, reset plan, or presentation that:

- omits the required demo labels;
- sets `production_claim=true` or attaches production, gate, customer-evidence, approval, execution, or reconciliation truth surfaces;
- treats fake credentials, sample credentials, demo tokens, demo certificates, demo source state, or fixture provenance as valid production credentials or production readiness;
- allows reset selectors to delete production, imported, customer-private, or unlabeled records;
- infers tenant, account, repository, issue, environment, customer, source, approval, execution, or reconciliation linkage from naming convention, path shape, comments, or nearby metadata; or
- presents demo records as customer truth, gate truth, production truth, approval truth, execution truth, reconciliation truth, or closeout truth.

## 7. Fixture Expectations

Fixture expectations live under `docs/deployment/fixtures/demo-seed/`.

| Fixture | Expected validity | Required rejection |
| --- | --- | --- |
| `valid-demo-seed.json` | `valid` | None |
| `missing-label.json` | `invalid` | missing required demo label |
| `destructive-reset.json` | `invalid` | reset deletes production records |
| `production-claim.json` | `invalid` | demo record claims production truth |

Negative fixtures must fail closed when a demo record lacks required labels, when reset can delete production records, or when a demo record is used as production truth.

## 8. Validation Rules

Validation must fail closed when:

- the demo seed contract is missing;
- any seed record type row is incomplete;
- any required demo label row is missing;
- reset selector, production guard, or failure cleanup coverage is missing;
- fixture expectations are missing;
- a negative fixture becomes valid;
- a valid fixture lacks required labels, demo mode, production exclusion, or reset safety;
- demo records are described as production truth, gate truth, customer evidence, approval truth, execution truth, reconciliation truth, or closeout truth;
- placeholder credentials, sample secrets, fake credentials, raw forwarded headers, or inferred scope bindings are treated as valid; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders such as `<demo-fixture-bundle>`, `<profile-name>`, `<supervisor-config-path>`, and `<codex-supervisor-root>`.

## 9. Forbidden Claims

- Demo data is production truth.
- Demo record is production truth.
- Demo seed output is gate truth.
- Demo reset may delete production records.
- Demo labels are optional.
- Fake credentials are valid credentials.
- Sample credentials are valid credentials.
- Demo source state is customer evidence.
- Demo approval is approval truth.
- Demo execution receipt is execution truth.
- Demo reconciliation note is reconciliation truth.
- This contract implements production data import.
- This contract implements Wazuh product profiles.
- This contract implements Shuffle product profiles.

## 10. Validation

Run `bash scripts/verify-phase-52-7-demo-seed-contract.sh`.

Run `bash scripts/test-verify-phase-52-7-demo-seed-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1070 --config <supervisor-config-path>`.

The verifier must fail when the demo seed contract is missing, when label, reset, fixture, production exclusion, or authority-boundary coverage is incomplete, when negative fixtures falsely pass, when demo records are treated as production truth, or when publishable guidance uses workstation-local absolute paths.

## 11. Non-Goals

- No first-user UI journey is implemented here.
- No production data import is implemented here.
- No Wazuh product profile or Shuffle product profile is implemented here.
- No RC behavior or GA behavior is implemented here.
- No demo record, demo label, fixture, reset output, fake secret, sample credential, demo source state, or operator-facing seed summary becomes production truth, gate truth, customer evidence, approval truth, execution truth, reconciliation truth, or closeout truth.
