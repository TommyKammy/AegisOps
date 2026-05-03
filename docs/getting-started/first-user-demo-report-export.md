# Phase 55.6 First-User Demo Report Export Skeleton

- **Status**: Accepted as Phase 55.6 first-user demo report export skeleton
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/getting-started/first-user-journey.md`, `docs/getting-started/first-30-minutes.md`, `docs/deployment/demo-seed-contract.md`, `docs/deployment/demo-reset-mode-separation.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1175, #1178, #1181

This skeleton defines demo-labeled report export output for the Phase 55 guided first-user journey only. It is the first-user report shape used to show a new operator how the journey can be summarized from directly linked demo records.

It does not implement commercial report breadth, audit export administration, RC proof export, production report templates, support bundles, customer evidence packets, or GA readiness.

## 1. Purpose

Demo report export output is demo evidence only. It helps the first user confirm the journey sequence after the demo alert, case, evidence, recommendation, action review, execution receipt, and reconciliation records are present.

This skeleton cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

## 2. Export Skeleton Contract

Every exported artifact must carry the labels `demo-only`, `first-user-rehearsal`, and `not-production-truth`. The report type must be `first-user-demo-report-export`, the mode must be `demo`, and the output must say it is demo evidence only.

Export output, generated files, report metadata, UI state, browser state, verifier output, and issue-lint output cannot become production truth or override authoritative workflow records. Missing records must be reported as unavailable follow-up items, not inferred from same-parent, sibling, browser, downstream, or operator-facing context.

## 3. Demo Journey References

The export skeleton must include directly linked demo alert, case, evidence, recommendation, action review, execution receipt, and reconciliation references when those records are available from the demo bundle.

| Reference | Source expectation | Export rule |
| --- | --- | --- |
| Demo alert | Directly linked demo alert record from the reviewed bundle. | Include record identifier, demo labels, source family, detection summary, and provenance pointer only. |
| Demo case | Directly linked case admitted from the demo alert. | Include case identifier, demo labels, status, and alert binding only. |
| Demo evidence | Directly linked evidence records bound to the demo case and alert. | Include evidence identifiers, demo labels, summary, and record binding only. |
| Demo recommendation | Directly linked recommendation for the demo case. | Include recommendation identifier, demo labels, advisory summary, and linked evidence only. |
| Demo action review | Directly linked action review for the proposed demo action. | Include review identifier, demo labels, reviewer decision boundary, approval requirement, and protected target summary only. |
| Demo execution receipt | Directly linked receipt returned for the approved demo action request. | Include receipt identifier, demo labels, execution outcome summary, and action binding only. |
| Demo reconciliation | Directly linked reconciliation result comparing the receipt with the approved request. | Include reconciliation identifier, demo labels, outcome summary, and receipt binding only. |

## 4. Secret Hygiene

Secret values, placeholder credentials, fake secrets, sample credentials, unsigned tokens, TODO values, bearer tokens, API keys, passwords, private keys, session cookies, and customer-specific credentials must not appear in exported output.

Exported text may name custody references or redaction posture, but it must not include raw secret material. When a required reference has a credential-bearing source field, the export must either omit the field or show a redaction marker that proves no secret value was exported.

## 5. Fixture Expectations

| Fixture | Expected validity | Required rejection |
| --- | --- | --- |
| `valid-demo-report-export.json` | valid | |
| `unavailable-follow-up-reference.json` | valid | |
| `non-object-payload.json` | invalid | invalid report export payload |
| `missing-demo-label.json` | invalid | missing required demo label |
| `invalid-authority-boundary.json` | invalid | invalid authority boundary |
| `secret-looking-value.json` | invalid | secret-looking value in export output |
| `key-secret-looking-value.json` | invalid | secret-looking value in export output |
| `commercial-report-claim.json` | invalid | demo export claims commercial report breadth |
| `production-truth-claim.json` | invalid | demo export claims production truth |
| `authority-override-claim.json` | invalid | demo export claims it can override authoritative records |
| `missing-reference-availability.json` | invalid | missing demo journey reference |

Negative fixtures must fail closed when the payload shape is invalid, the demo label is missing, the authority-boundary object is malformed, secret-looking values are present, commercial reporting breadth is claimed, or output is presented as production truth.

## 6. Validation Rules

The focused verifier must fail when:

- the skeleton document is missing;
- required headings, labels, issue links, authority-boundary text, validation commands, or direct-reference rows are missing;
- a forbidden claim appears outside the forbidden-claims section;
- fixtures are missing or do not match their expected validity;
- a fixture with secret-looking output passes validation;
- a fixture claims commercial report breadth, audit export completeness, RC proof, GA readiness, or production truth; or
- publishable guidance uses workstation-local absolute paths.

## 7. Forbidden Claims

These statements are intentionally forbidden outside this section:

- Demo report export is production truth.
- Demo report export is commercial reporting completeness.
- Demo report export is audit export completeness.
- Demo report export is RC proof.
- Demo report export is GA readiness.
- Demo report export is commercial readiness.
- Demo export may include secrets.
- Demo export may include credentials.
- Report metadata overrides authoritative records.
- Generated report files override authoritative records.

## 8. Validation

Run `bash scripts/verify-phase-55-6-first-user-report-export-skeleton.sh`.

Run `bash scripts/test-verify-phase-55-6-first-user-report-export-skeleton.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1181 --config <supervisor-config-path>`.

## 9. Non-Goals

- No commercial report breadth is approved here.
- No audit export administration is approved here.
- No RC proof export is approved here.
- No production report templates are approved here.
- No secret-bearing support bundle is approved here.
- No demo report, generated file, report metadata, UI state, browser state, verifier output, or issue-lint output becomes production truth, gate truth, audit truth, approval truth, execution truth, reconciliation truth, closeout truth, or authoritative workflow truth.
