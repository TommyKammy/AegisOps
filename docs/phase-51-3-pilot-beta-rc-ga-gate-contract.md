# Phase 51.3 Pilot, Beta, RC, and GA Gate Contract

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0011-phase-51-1-replacement-boundary.md`, `docs/deployment/pilot-readiness-checklist.md`
- **Related Issues**: #1041, #1042, #1044

This contract defines the evidence required before AegisOps may advance from the current pilot foundation toward commercial replacement readiness. It changes documentation and verification only. It does not implement installer, Wazuh profile, Shuffle profile, AI, supportability, packaging, release-candidate, or general-availability workflows.

## 1. Gate Names

The only approved readiness gate names for the Phase 51 replacement-readiness roadmap are:

| Gate | Meaning | Release-state boundary |
| --- | --- | --- |
| Pilot | Single-customer or tightly controlled design-partner validation of the governed operating experience. | Pre-commercial and pre-GA. |
| Beta | Multi-operator or expanded design-partner validation with repeatable evidence capture and named limitation owners. | Still pre-RC and pre-GA. |
| RC | Replacement candidate readiness for the intended SMB operating scope, pending final GA evidence and launch decisions. | Phase 66 is RC. |
| GA | General availability replacement readiness supported by real-user or design-partner evidence, supportability, and known limitation ownership. | Phase 67 is GA. |

Phase 66 is RC. Phase 67 is GA.

Phase 51.7 materialization guard can use the gate names `Pilot`, `Beta`, `RC`, and `GA` from this contract when it validates later roadmap or issue materialization.

## 2. Shared Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, and limitation truth.

Gate evidence must prove AegisOps records remain authoritative. Wazuh, Shuffle, AI, tickets, evidence systems, dashboards, demo data, browser state, UI cache, downstream receipts, and operator-facing summaries cannot satisfy a gate by acting as workflow truth.

Wazuh evidence is accepted only as subordinate detection signal evidence after explicit AegisOps admission and linkage.

Shuffle evidence is accepted only as subordinate delegated execution evidence after explicit AegisOps approval, action intent, execution receipt, and reconciliation linkage.

AI evidence is accepted only as subordinate advisory trace evidence; AI must not approve actions, execute actions, reconcile execution, close cases, activate detectors, or become source truth.

Ticket or external evidence-system references are accepted only as coordination or custody context linked to authoritative AegisOps records. Ticket status, evidence-system status, and downstream receipt status must not replace AegisOps case, approval, reconciliation, release, gate, or limitation records.

Gate packets must use repo-relative commands, documented env vars, and placeholders such as `<runtime-env-file>`, `<evidence-dir>`, `<release-gate-manifest.md>`, `<support-bundle.md>`, `<upgrade-plan.md>`, and `<design-partner-evidence.md>`.

## 3. Evidence Families

Each gate packet must explicitly include or explicitly refuse with owner and follow-up date these evidence families:

| Evidence family | Required content | Authority-boundary proof |
| --- | --- | --- |
| Install evidence | Reviewed install or upgrade entry command, selected profile, operator, revision, environment class, and retained output path. | Install success is not accepted unless the resulting AegisOps readiness and record-chain checks bind to the same gate record. |
| Wazuh signal evidence | Wazuh manager, rule or decoder scope, source-family parser coverage, sample signal identifier, AegisOps alert identifier, and admission review result. | Wazuh remains the detection substrate; raw Wazuh alert state does not become AegisOps alert, case, or release truth. |
| Shuffle execution evidence | Workflow identifier, delegated action request, approval record, execution receipt, reconciliation result, mismatch handling, and rollback owner. | Shuffle remains the routine automation substrate; workflow success does not become reconciliation truth without an AegisOps reconciliation record. |
| AI trace evidence | Prompt or tool policy version, advisory output identifier, reviewed recommendation identifier, human decision, and refused autonomous action scope. | AI remains advisory-only and cannot approve, execute, reconcile, close, activate, or define source truth. |
| Report export evidence | Export command, export artifact reference, report schema version, redaction review, and source record identifiers. | Reports are derived surfaces and must cite authoritative AegisOps records instead of becoming independent state. |
| Restore dry-run evidence | Restore point, restore target, clean-state validation, reviewed record-chain replay, failed-path cleanup result, and retained manifest. | Restore acceptance comes from committed AegisOps state and clean-state evidence, not substrate-local backup names or inferred environment naming. |
| Upgrade plan evidence | Version boundary, migration owner, rollback decision point, expected smoke checks, retained upgrade evidence path, and known compatibility risks. | Upgrade success is not accepted until AegisOps readiness, record-chain, and reconciliation checks pass against the target revision. |
| Support bundle evidence | Support bundle command, redaction review, included record identifiers, omitted private data classes, owner, and retention expectation. | Support bundles are evidence packages only and cannot replace authoritative AegisOps gate, case, release, or limitation records. |
| Limitations ownership evidence | Known limitation, affected gate, owner, acceptance or refusal reason, follow-up date, and customer or operator impact. | Limitations remain explicit AegisOps-owned records; unresolved limitations cannot be hidden in tickets, report prose, or roadmap summaries. |

Missing, malformed, mixed-snapshot, placeholder-backed, or subordinate-authority evidence blocks the gate until the prerequisite is supplied or explicitly refused with an owner and follow-up date.

## 4. Pilot Gate

Pilot gate is documented with required evidence.

Pilot entry requires install evidence, Wazuh signal evidence, Shuffle execution evidence when delegated execution is in scope, AI trace evidence when assistant recommendations are presented, report export evidence, restore dry-run evidence, upgrade plan evidence, support bundle evidence, and limitations ownership evidence.

Pilot evidence may be single-customer or tightly controlled design-partner evidence. It proves a governed pilot operating path only. It does not prove RC replacement readiness, GA replacement readiness, self-service commercial readiness, broad SIEM/SOAR coverage, multi-customer operations, formal SLA coverage, or 24x7 support.

Pilot must reject broad GA overclaim before evidence exists.

## 5. Beta Gate

Beta gate is documented with required evidence.

Beta entry requires all Pilot evidence plus repeatability evidence across expanded operator or design-partner use, documented limitation disposition, support-bundle rehearsal evidence, upgrade-plan rehearsal evidence, and at least one gate packet that proves the same evidence families can be collected without relying on demo-only data.

Beta evidence must still keep AegisOps records authoritative. Beta does not approve RC replacement readiness, GA replacement readiness, self-service commercial readiness, formal SLA coverage, or broad SIEM/SOAR coverage.

Beta must reject broad GA overclaim before evidence exists.

## 6. RC Gate

RC gate is documented with required evidence.

RC replacement readiness means the intended SMB operating scope has complete gate packets for install, Wazuh signal, Shuffle execution, AI trace, report export, restore dry-run, upgrade plan, support bundle, and limitations ownership evidence; all blocking limitations have accepted owners and decision dates; and the replacement boundary from `docs/adr/0011-phase-51-1-replacement-boundary.md` is still preserved.

RC is not GA. RC allows a release-candidate replacement claim only for the explicitly reviewed SMB operating scope and only while the remaining GA evidence is tracked as a named prerequisite.

Phase 66 is RC and must not be described as GA.

RC must reject broad GA overclaim before evidence exists.

## 7. GA Gate

GA gate is documented with required real-user or design-partner evidence.

GA replacement readiness requires all RC evidence plus real-user or design-partner evidence that the reviewed operating experience worked across the intended launch scope, including install or upgrade, Wazuh signal admission, Shuffle delegated execution, AI advisory trace review, report export, restore dry-run, upgrade plan rehearsal, support bundle generation, and accepted limitations ownership.

GA evidence must include the real-user or design-partner record reference, reviewed environment class, operator or design-partner owner, date, gate record identifier, accepted limitations, support owner, upgrade owner, and follow-up decision.

Phase 67 is GA and must not be materialized until the GA gate evidence exists.

GA must reject broad GA overclaim before real-user or design-partner evidence exists.

## 8. Forbidden Claims

The gate contract rejects broad GA overclaim before evidence exists.

Forbidden claims:

- AegisOps is already GA.
- AegisOps is already a self-service commercial replacement.
- AegisOps is GA because Wazuh emitted alerts.
- AegisOps is GA because Shuffle ran workflows.
- AegisOps is GA because AI produced recommendations.
- AegisOps is GA because tickets were closed.
- Phase 66 is GA.
- RC and GA are interchangeable.
- GA can be claimed without real-user or design-partner evidence.
- Wazuh, Shuffle, AI, tickets, evidence systems, dashboards, demo data, browser state, UI cache, downstream receipts, or operator-facing summaries are authoritative for gate acceptance.

## 9. Validation

Run `bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh`.

Run `bash scripts/test-verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1044 --config <supervisor-config-path>`.

The verifier must fail when the Pilot, Beta, RC, or GA gate is missing; when Phase 66 is not identified as RC; when Phase 67 is not identified as GA; when RC and GA are not distinguished; when GA is claimed without real-user or design-partner evidence; or when Wazuh, Shuffle, AI, tickets, evidence systems, dashboards, demo data, browser state, UI cache, downstream receipts, or operator-facing summaries are promoted into authority.

## 10. Non-Goals

- No installer, Wazuh profile, Shuffle profile, AI, supportability, packaging, release-candidate, or general-availability workflow is implemented by this contract.
- No runtime behavior, release status, customer contract, SLA, support plan, or commercial launch status changes.
- No external substrate, assistant, ticket, evidence system, dashboard, demo data, browser state, UI cache, downstream receipt, or operator-facing summary becomes authoritative workflow truth.
