# Phase 38 Release Handoff Evidence Manifest - Filled Redacted Single-Customer Pilot Example

This filled exemplar shows the expected retained packet shape for one single-customer pilot release. It is intentionally redacted and contains no customer secrets, customer-private payloads, raw customer logs, workstation-local paths, live credentials, bootstrap tokens, or private ticket content.

Release readiness summary: Pilot release accepted for one redacted customer environment after reviewed preflight, smoke, restore, rollback, upgrade, and known-limitations evidence all referenced the same release identifier. AegisOps control-plane records and release-gate evidence remain the workflow truth for the launch decision.

Release bundle identifier: aegisops-single-customer-pilot-2026-04-27-c4527e5

Install preflight result: docs/deployment/evidence-examples/single-customer-pilot/install-preflight-result.redacted.md records PASS for `scripts/verify-single-customer-install-preflight.sh --env-file <runtime-env-file>`. The retained result confirms required runtime env shape, secret-source references, reverse-proxy expectation, and startup prerequisites without storing secret values.

Runtime smoke result: docs/deployment/evidence-examples/single-customer-pilot/runtime-smoke/manifest.md records PASS for `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>`. The smoke manifest covers readiness, protected read-only reachability, queue sanity, and first low-risk action preconditions for this release identifier.

Backup restore rollback upgrade rehearsal: docs/deployment/evidence-examples/single-customer-pilot/release-gate-manifest.md records backup custody, selected restore point, restore validation, same-day rollback-not-needed decision, post-upgrade smoke, reviewed record-chain evidence, and clean-state validation for the same release identifier.

Known limitations: docs/deployment/evidence-examples/single-customer-pilot/known-limitations.redacted.md records accepted limitations, non-blocking follow-up owners, and rollback acceptance criteria. The reviewed limitation set does not approve direct backend access, optional-extension launch gates, external ticket authority, or assistant-owned workflow action.

Rollback instructions: docs/runbook.md#43-rollback-and-restore references the reviewed rollback path and selected restore point for this release identifier. Recovery target selection comes from the release-gate manifest, not from memory, ticket status, substrate-local names, or inferred environment naming.

Handoff owner: pilot-owner-redacted, IT Operations, Information Systems Department.

Next health review: 2026-04-28 business-day health review, queue review, and backup-drift check owned by pilot-owner-redacted. The follow-up review must confirm queue state, readiness state, backup job outcome, known-limitation follow-ups, and whether any refused or missing evidence still blocks broader rollout.

Refused or missing evidence handling: Customer-private raw log payloads, credential screenshots, browser session captures, raw forwarded-header values, unsigned identity hints, and ticket-private conversation exports were refused for the retained packet. The packet retains redacted evidence summaries, AegisOps record identifiers, release-gate references, and clean-state validation instead of substituting private data or treating absence as success.

Missing evidence outcome: A customer-private payload request is marked refused and non-substitutable. If later review requires the payload, pilot expansion remains blocked until an approved redacted evidence source is retained; the current handoff does not infer success from the missing artifact.

Subordinate context only: Wazuh alert references, Shuffle execution receipts, Zammad ticket links, assistant notes, ML shadow observations, downstream receipts, optional endpoint evidence, optional network evidence, and optional extension health are retained as context only. They do not own release readiness, case state, approval, execution, reconciliation, restore, rollback, pilot entry, or handoff truth.

Authority boundary: AegisOps approval, evidence, execution, reconciliation, readiness, and recovery records remain authoritative; external records are subordinate context only.
