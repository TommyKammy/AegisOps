# AegisOps Phase 63.1 Evidence Source Registry v1

## 1. Purpose

Phase 63.1 defines the first bounded evidence source registry for Evidence Expansion v1.

The registry permits osquery plus one bounded intel/enrichment source only. It records source id, type, owner, allowed target class, custody requirements, freshness window, confidence posture, and disabled or degraded states before any Phase 63 evidence pack can cite the source.

This contract keeps AegisOps-owned records authoritative. Evidence sources, source-native state, evidence packs, enrichment output, AI output, verifier output, issue-lint output, browser state, and UI cache remain subordinate context only.

## 2. Registry Entries

| Source id | Source type | Owner | Allowed target class | Custody requirements | Freshness window | Confidence posture | Disabled and degraded states |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `osquery_host_state` | `osquery` | IT Operations, Information Systems Department | `explicitly_bound_host` | Reviewed query id, operator or automation attribution, collection timestamp, host binding, and AegisOps evidence record id. | `PT24H` | Observed host state subordinate context only. | Degraded when host binding or collection freshness is incomplete; disabled by policy or missing custody. |
| `malwarebazaar_hash_reputation` | `malwarebazaar_hash_reputation` | IT Operations, Information Systems Department | `reviewed_file_hash` | Reviewed file hash, enrichment request id, collection timestamp, response digest, and AegisOps evidence record id. | `PT6H` | External hash reputation subordinate context only. | Degraded when reputation freshness or response digest is incomplete; disabled by policy or missing hash custody. |

## 3. Selected Bounded Enrichment Rationale

`malwarebazaar_hash_reputation` is the selected bounded intel/enrichment source because it is limited to reviewed file-hash reputation context. It does not add broad MISP, IntelOwl, Suricata, Velociraptor, YARA, capa, public-internet pivot, or evidence-source marketplace breadth.

The enrichment result can support analyst review only after the file hash is already linked to an AegisOps evidence record with custody and scope binding. It cannot create alert truth, case truth, source truth, approval truth, execution truth, reconciliation truth, detector activation truth, release truth, gate truth, closeout truth, or readiness truth.

## 4. Boundedness Rules

- The registry must stay bounded to `osquery_host_state` and `malwarebazaar_hash_reputation`.
- Broad or default evidence source lists are rejected.
- Unsupported broad sources are rejected, including Velociraptor, YARA, capa, MISP breadth, Suricata, and IntelOwl breadth.
- Missing owner, missing freshness window, missing custody requirements, missing allowed target class, disabled source use, degraded source use, and target-class mismatch fail closed.
- Source types outside `osquery` and `malwarebazaar_hash_reputation` are rejected.
- Registry entries that claim workflow authority are rejected across source id, source type, owner, target class, custody, freshness, confidence, status, degraded states, disabled states, and authority posture fields.
- Unknown mapping fields are rejected before coercion so ignored JSON keys cannot smuggle broad source lists or workflow-authority claims.
- Custody requirements are source-specific: osquery must keep reviewed query, collection timestamp, host binding, and AegisOps evidence record custody; MalwareBazaar must keep reviewed hash, enrichment request, collection timestamp, response digest, and AegisOps evidence record custody.

## 5. Authority Boundary

Only AegisOps-owned records own workflow truth for admitted alerts, cases, evidence requests, approvals, action requests, execution receipts, reconciliation, audit, release gates, limitations, and closeout state.

This registry cannot let osquery output, hash-reputation output, source-native state, evidence packs, freshness or confidence projections, UI state, browser state, AI output, verifier output, or issue-lint output approve, execute, reconcile, close, activate detectors, create source truth, gate release, or claim readiness.

The negative-test posture follows `docs/phase-51-6-authority-boundary-negative-test-policy.md` for endpoint evidence, evidence systems, demo data, UI cache, browser state, AI output, verifier output, and issue-lint output.

## 6. Validation

- Run `bash scripts/verify-phase-63-1-evidence-source-registry-v1.sh`.
- Run `python3 -m unittest control-plane.tests.test_phase63_evidence_source_registry`.
- Run `bash scripts/verify-publishable-path-hygiene.sh`.
- Run `node <codex-supervisor-root>/dist/index.js issue-lint 1332 --config <supervisor-config-path>`.
