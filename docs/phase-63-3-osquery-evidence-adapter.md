# AegisOps Phase 63.3 Osquery Evidence Adapter MVP

## 1. Purpose

Phase 63.3 adds a bounded osquery evidence adapter MVP for Evidence Expansion v1.

The adapter turns reviewed osquery host-state, process-context, and state-context output into subordinate evidence packs only after a reviewed Phase 63 evidence request record binds the case, target host, source, scope, custody, authorization, and expiry.

The adapter does not add endpoint remediation, containment, direct command authority, source-native truth, Controlled Write, Hard Write, Beta readiness, RC readiness, GA readiness, commercial replacement readiness, or Phase 64/65/66/67 work.

## 2. Adapter Contract

The adapter entry point is `OsqueryEvidenceAdapter.build_evidence_pack`.

Required input:

- `ReviewedEvidenceRequestRecord` with `source_id` set to `osquery_host_state`.
- Explicit `host_identifier` matching the reviewed request target.
- Reviewed `query_id`, `query_name`, and result kind.
- Osquery rows represented as a sequence of mappings.
- Timezone-aware `collected_at`.
- Osquery custody with reviewed query id, collector identity, collection timestamp, host binding, and AegisOps evidence record id.
- Adapter state of `available` or `unavailable`.
- Read-only requested operation.

The MVP result kinds are `host_state`, `process`, and `state_context`.

## 3. Status And Freshness

Fresh osquery output within the Phase 63.1 `osquery_host_state` freshness window returns an `available` pack.

Osquery output older than the registry freshness window returns a `degraded` pack with `stale_collection`. Stale output remains subordinate context and cannot become case truth, source truth, approval truth, execution truth, reconciliation truth, closeout truth, release truth, gate truth, or readiness truth.

Unavailable adapter state returns an `unavailable` pack with `adapter_unavailable` and no rows. The unavailable pack remains linked to the reviewed request and custody fields so operators can see the prerequisite failure without inventing source truth.

The adapter rejects osquery output whose `query_id` does not match the reviewed query id in custody. It also requires custody `collection_timestamp` to parse as a timezone-aware timestamp and match `collected_at`.

Osquery rows are bounded before whole-pack serialization: at most 500 rows, 128 distinct columns, 256 bytes per serialized column name, and 4096 bytes per serialized cell value.

Malformed rows, oversized rows, oversized column names, non-finite row values, malformed custody extras, unsupported result kinds, unauthorized, terminal, or expired reviewed requests, target mismatch, missing custody, custody query mismatch, custody host mismatch, custody timestamp mismatch, naive timestamps, and non-read-only operations fail closed.

## 4. Authority Boundary

Only AegisOps-owned records own workflow truth for admitted alerts, cases, evidence requests, approvals, action requests, execution receipts, reconciliation, audit, release gates, limitations, and closeout state.

Osquery output, evidence packs, source-native state, freshness projections, AI output, verifier output, issue-lint output, browser state, UI cache, and adapter state remain subordinate context only.

The adapter cannot approve, execute, reconcile, close, activate detectors, create source truth, gate release, claim readiness, remediate endpoints, contain hosts, quarantine files, kill processes, mutate protected targets, or issue direct command authority.

The negative-test posture follows `docs/phase-51-6-authority-boundary-negative-test-policy.md` for endpoint evidence, evidence systems, browser state, UI cache, AI output, verifier output, issue-lint output, and source-native state.

## 5. Validation

- Run `bash scripts/verify-phase-63-3-osquery-evidence-adapter.sh`.
- Run `python3 -m unittest control-plane.tests.test_phase63_3_osquery_evidence_adapter`.
- Run `bash scripts/verify-publishable-path-hygiene.sh`.
- Run `node <codex-supervisor-root>/dist/index.js issue-lint 1334 --config <supervisor-config-path>`.
