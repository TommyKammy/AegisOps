# AegisOps Phase 63.4 Bounded Intel Enrichment Adapter MVP

## 1. Purpose

Phase 63.4 adds the bounded intel/enrichment adapter MVP for Evidence Expansion v1.

The selected source is `malwarebazaar_hash_reputation`, matching the Phase 63.1 source registry. The selection is intentionally limited to reviewed file-hash reputation context. It does not add broad MISP, IntelOwl, Suricata, Velociraptor, YARA, capa, public-internet pivot, arbitrary enrichment marketplace, endpoint remediation, containment, direct command authority, source-native truth, Controlled Write, Hard Write, Beta readiness, RC readiness, GA readiness, commercial replacement readiness, or Phase 64/65/66/67 work.

## 2. Adapter Contract

The adapter entry point is `BoundedEnrichmentAdapter.build_evidence_pack`.

Required input:

- `ReviewedEvidenceRequestRecord` with `source_id` set to `malwarebazaar_hash_reputation`.
- Explicit `file_hash` matching the reviewed request target and MalwareBazaar response hash.
- Timezone-aware `looked_up_at`.
- MalwareBazaar hash reputation response represented as a mapping.
- Enrichment custody with reviewed file hash, enrichment request id, collection timestamp, canonical response digest, and AegisOps evidence record id.
- Adapter state of `available` or `unavailable`.
- Read-only requested operation `lookup_hash_reputation`.

The MVP output is a subordinate evidence pack with source provenance, confidence posture, freshness state, unavailable state, degraded reasons, and an explicit no-authority boundary.

## 3. Status, Confidence, And Freshness

Fresh MalwareBazaar hash reputation output within the Phase 63.1 `malwarebazaar_hash_reputation` freshness window returns an `available` pack.

Hash reputation output older than the registry freshness window returns a `degraded` pack with `stale_reputation`. Conflicting enrichment returns a `degraded` pack with `conflicting_enrichment` and an unresolved confidence ambiguity badge. Stale or conflicting enrichment remains subordinate context and cannot become case truth, source truth, approval truth, execution truth, reconciliation truth, closeout truth, release truth, gate truth, or readiness truth.

Unavailable source state returns an `unavailable` pack with `source_unavailable` and no response body. The unavailable pack remains linked to the reviewed request and custody fields so operators can see the prerequisite failure without inventing source truth.

The adapter is fixed to the `malwarebazaar_hash_reputation` source and rejects attempts to rebind the adapter or reviewed request to another evidence source. It rejects responses whose hash does not match the reviewed file hash and rejects custody `response_digest` values that do not match the canonical JSON digest of the response. It also requires custody `collection_timestamp` to parse as a timezone-aware timestamp and match `looked_up_at`.

Missing custody, source mismatch, hash mismatch, response digest mismatch, collection before request review, future lookup timestamps, unavailable malformed states, non-read-only operations, and enrichment responses or response field names that claim workflow authority fail closed.

## 4. Authority Boundary

Only AegisOps-owned records own workflow truth for admitted alerts, cases, evidence requests, approvals, action requests, execution receipts, reconciliation, audit, release gates, limitations, and closeout state.

MalwareBazaar output, enrichment output, confidence scores, freshness projections, evidence packs, source-native state, AI output, verifier output, issue-lint output, browser state, UI cache, and adapter state remain subordinate context only.

The adapter cannot approve, execute, reconcile, close, activate detectors, create source truth, gate release, claim readiness, remediate endpoints, contain hosts, quarantine files, kill processes, mutate protected targets, or issue direct command authority.

The negative-test posture follows `docs/phase-51-6-authority-boundary-negative-test-policy.md` for endpoint evidence, evidence systems, browser state, UI cache, AI output, verifier output, issue-lint output, and source-native state.

## 5. Validation

- Run `bash scripts/verify-phase-63-4-bounded-enrichment-adapter.sh`.
- Run `python3 -m unittest control-plane.tests.test_phase63_4_bounded_enrichment_adapter`.
- Run `bash scripts/verify-publishable-path-hygiene.sh`.
- Run `node <codex-supervisor-root>/dist/index.js issue-lint 1335 --config <supervisor-config-path>`.
