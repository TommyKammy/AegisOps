# Detector Activation Evidence Handoff - Filled Redacted Single-Customer Pilot Example

This filled exemplar shows the expected retained packet shape for one single-customer pilot detector activation review. It is intentionally redacted and contains no customer secrets, customer-private logs, raw customer payloads, workstation-local paths, live credentials, bootstrap tokens, or private ticket content.

Release identifier: aegisops-single-customer-pilot-2026-04-27-c4527e5

Candidate rule identifier: github-audit-privilege-change

Source-family package: GitHub audit via reviewed Wazuh-backed intake boundary

Lifecycle state: staging-review-accepted

Activation owner: pilot-detector-owner-redacted

Disable owner: pilot-disable-owner-redacted

Rollback owner: pilot-rollback-owner-redacted

Expected alert volume: 0-3 alerts per business day during the first pilot week

Expected benign cases: Reviewed repository administration, approved maintainer changes, access review cleanup, automation identity maintenance, scheduled change windows, onboarding, and offboarding activity.

False-positive review: Routine repository administration, access review cleanup, automation identity behavior, and scheduled maintenance were reviewed as expected benign cases. Benign handling still requires explicit AegisOps record linkage or reviewed GitHub audit evidence; familiar actor, team, repository, workflow, or organization names are not enough to suppress the candidate.

Next-review date: 2026-05-04

Fixture evidence: control-plane/tests/fixtures/wazuh/github-audit-alert.json

Parser evidence: decoder.name `github_audit`, rule.id `github-audit-privilege-change`, and source-family parser coverage verified by the GitHub audit detector activation candidate tests

Validation command result: PASS for `bash scripts/verify-github-audit-detector-activation-candidate.sh`

Wazuh substrate evidence: Wazuh manager `wazuh-manager-github-1`, decoder `github_audit`, rule `github-audit-privilege-change`, and fixture-backed GitHub audit fields are evidence for admission review only

AegisOps analytic signal admission: AegisOps alert `alert-redacted-github-admin-0001`, case `case-redacted-github-admin-0001`, evidence `evidence-redacted-github-admin-0001`, and release-gate record `release-gate-redacted-2026-04-27` are the control-plane records used for handoff review

Authority boundary: Wazuh rule state, raw Wazuh alerts, GitHub audit fields, OpenSearch state, Zammad tickets, and downstream detector receipts remain subordinate evidence; AegisOps-owned alert, case, evidence, reconciliation, and release-gate records remain workflow truth.

Disable path: Move the candidate back to `candidate`, remove it from the reviewed pilot detector scope, and preserve the refused or disabled outcome in the release-gate evidence record before the next health review.

Rollback path: Restore the last reviewed fixture set and candidate revision, rerun `bash scripts/verify-github-audit-detector-activation-candidate.sh`, and keep pilot entry blocked if parser evidence, Wazuh provenance, or AegisOps record linkage is missing.

False-positive follow-up: The pilot detector owner reviews the first-week alert set against approved maintainer activity, access review cleanup, and automation identity behavior. Any event without explicit AegisOps linkage, reviewed GitHub audit evidence, and Wazuh provenance remains suspicious or blocked rather than being suppressed by naming convention.

Known limitations: The exemplar covers only the GitHub audit repository administrator membership-change candidate for one pilot release. It does not activate Entra ID, Microsoft 365 audit, endpoint, network, broad detector catalog, automatic detector deployment, direct GitHub API actioning, or live source-side mutation.

Clean-state outcome: Rejected activation attempts must leave no orphan alert, partial case, partial durable write, or misleading handoff evidence.
