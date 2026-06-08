# Phase 66.2 Wazuh Sample Signal RC Proof

- **Status**: Accepted as the Phase 66.2 Wazuh sample signal RC proof contract for release-candidate evidence planning only.
- **Date**: 2026-06-08 Asia/Tokyo
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-66-1-clean-host-rc-e2e-harness.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/deployment/wazuh-manager-intake-binding-contract.md`, `docs/deployment/wazuh-source-health-projection-contract.md`, `docs/deployment/wazuh-authority-boundary-negative-tests.md`, `docs/phase-65-closeout-evaluation.md`
- **Related Issues**: #1397, #1399

This contract defines the Phase 66.2 Wazuh sample signal RC proof surface. It records how one reviewed Wazuh-origin sample signal reaches AegisOps as subordinate analytic-signal evidence during the Phase 66 RC journey.

The proof depends on the Phase 66.1 clean-host RC E2E harness. It does not replace the clean-host journey, and it does not satisfy the later Shuffle, AI, report export, supportability, authority-boundary proof-pack, closeout, or GA evidence slices.

## 1. Proof Purpose

The Wazuh sample signal proof demonstrates that a sample Wazuh-origin signal can be observed, health-checked, admitted, and linked by AegisOps without turning Wazuh into alert truth, case truth, source truth, release truth, gate truth, or workflow authority.

This proof is RC evidence only. It is not broad Wazuh detector parity, production monitoring coverage, production customer telemetry import, source-native truth, GA readiness, real design-partner success, or commercial replacement readiness.

## 2. Sample Signal Evidence

Every Phase 66.2 proof packet must include these fields:

| Field | Required evidence | Failure boundary |
| --- | --- | --- |
| `journey_run_id` | The Phase 66.1 run identifier that observed the sample signal. | Missing or mismatched run identifiers fail the proof. |
| `repository_revision` | Immutable repository revision for the proof packet. | Mutable branch names fail the proof. |
| `wazuh_profile` | `smb-single-node` Wazuh product profile reference. | Any other profile is out of scope. |
| `sample_signal_id` | Stable sample signal identifier. | Dashboard text or filenames cannot create signal identity. |
| `source_family` | Wazuh source family and parser family. | Source family cannot be inferred from nearby prose. |
| `source_health_reference` | Reviewed source-health projection record or artifact reference. | Wazuh health is subordinate context only. |
| `intake_binding_reference` | Reviewed `/intake/wazuh` binding and proxy route reference. | Direct or ad hoc intake paths fail the proof. |
| `admission_record_id` | AegisOps admission record for the sample signal. | Wazuh alerts remain candidate signals until admission. |
| `aegisops_alert_id` | AegisOps alert identifier created or linked after admission. | Wazuh alert ids are not AegisOps alert truth. |
| `provenance_reference` | Explicit Wazuh manager, rule, event, timestamp, proxy, and custody provenance. | Raw forwarded headers or inferred linkage fail the proof. |
| `case_linking_posture` | `not_linked`, `linked_by_aegisops_case_workflow`, or `explicitly_deferred`. | Wazuh cannot promote, close, or mutate cases. |
| `limitation_references` | Known limitation ids, owner, decision date, and follow-up date when evidence is incomplete. | Missing limitations cannot be hidden in source-health text. |

## 3. Source Health And Admission

The proof must cite `docs/deployment/wazuh-source-health-projection-contract.md` and include source-health evidence for manager, dashboard, indexer, intake, signal freshness, parser, volume, and credential posture.

The proof must cite `docs/deployment/wazuh-manager-intake-binding-contract.md` and include explicit provenance fields for source family, source system, source component, source id, event id, event timestamp, Wazuh manager id, Wazuh rule id, Wazuh rule level, ingest channel, admission channel, secret custody reference, proxy route, and reviewer.

Admission succeeds only after AegisOps creates or links an admission record and alert record. Wazuh manager state, Wazuh dashboard state, Wazuh alert status, Wazuh rule state, webhook acknowledgement, source-health projection, verifier output, and issue-lint output remain subordinate evidence.

## 4. Authority Boundary

AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, source admission, and closeout truth.

Wazuh remains a subordinate analytic-signal source. Wazuh alerts, Wazuh manager state, Wazuh dashboard state, Wazuh indexer contents, Wazuh source health, Wazuh rule state, Wazuh timestamps, webhook acknowledgements, generated config, tickets, AI output, browser state, UI cache, verifier output, issue-lint output, and downstream receipts cannot approve, execute, reconcile, close, release, gate, or mutate AegisOps records.

The proof must reject missing sample signal identity, missing source-health reference, missing intake binding reference, missing admission record, missing provenance, missing limitation references, source-native truth, broad SIEM parity, workstation-local paths, production secrets, customer-private data, inferred RC pass, inferred GA pass, verifier-as-readiness-truth, and issue-lint-as-readiness-truth.

## 5. Accepted Limitations

Phase 66.2 proves one reviewed Wazuh sample signal path for RC evidence. It does not prove broad Wazuh detector parity, production customer telemetry import, production monitoring coverage, real design-partner success, source-native truth, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness.

Later Phase 66 issues must still prove Shuffle sample execution, AI-assisted triage, report export, supportability, RC authority-boundary proof pack, and closeout evidence independently.

## 6. Verification

Run `bash scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh`.

Run `bash scripts/test-verify-phase-66-2-wazuh-sample-signal-rc-proof.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1399 --config <supervisor-config-path>`.
