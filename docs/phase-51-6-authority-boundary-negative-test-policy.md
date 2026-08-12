# Phase 51.6 Authority-Boundary Negative-Test Policy

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0011-phase-51-1-replacement-boundary.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-51-5-competitive-gap-matrix.md`
- **Related Issues**: #1041, #1042, #1047

This policy defines cross-phase negative-test expectations only. It does not implement AI, Wazuh, Shuffle, ticket, evidence, browser, UI, downstream receipt, demo-data, SIEM, SOAR, installer, release, or runtime behavior.

## 1. Purpose

Phase 51.6 records the authority-boundary negative-test policy that later breadth issues must cite before adding AI, Wazuh, Shuffle, ticket, evidence, browser, UI cache, downstream receipt, or demo-data behavior.

The purpose is to make the unsafe shortcut testable before breadth expands. Later issues must prove that subordinate surfaces stay subordinate when the system is asked to use them as approval, execution, reconciliation, case closure, source truth, gate truth, or production truth.

## 2. Authority Boundary

Only AegisOps-owned records own workflow truth for admitted alerts, cases, evidence, recommendations, approvals, action requests, execution receipts, reconciliation, audit, release gates, limitations, and closeout state.

Every subordinate surface must fail closed when asked to become approval, execution, reconciliation, case closure, source truth, gate truth, or production truth.

The subordinate surfaces covered by this policy are AI, Wazuh, Shuffle, tickets, endpoint evidence, network evidence, external evidence systems, browser state, UI cache, downstream receipts, and demo data.

Missing, malformed, placeholder-backed, mixed-snapshot, unsigned, unbound, stale, inferred, or partially trusted subordinate signals must reject the path, keep the guard in place, or surface an explicit prerequisite. They must not silently succeed, degrade to allow, or substitute guessed context.

## 3. Required Negative-Test Classes

Later breadth issues must include the narrowest negative test at the real enforcement boundary for each subordinate surface they touch.

| Surface | Required negative-test class | Expected fail-closed behavior |
| --- | --- | --- |
| AI | AI output, tool suggestions, summaries, or recommendations are presented as approval, execution, reconciliation, case closure, detector activation, or source truth. | Reject the shortcut and require an explicit AegisOps record, human decision, or reviewed prerequisite. |
| Wazuh | Wazuh alert, rule, manager, decoder, status, or timestamp state is presented as AegisOps alert, case, evidence, reconciliation, release, or gate truth without explicit admission and linkage. | Reject the shortcut and require an admitted AegisOps record linked to the Wazuh signal. |
| Shuffle | Shuffle workflow success, failure, retry, payload, or callback state is presented as AegisOps execution receipt, reconciliation, case closure, release, or gate truth without AegisOps approval, action intent, receipt, and reconciliation records. | Reject the shortcut and keep reconciliation open or mismatched until the AegisOps record chain closes it. |
| Tickets | Ticket open, closed, escalated, assigned, commented, or SLA state is presented as AegisOps case, approval, reconciliation, limitation, release, or gate truth. | Reject the shortcut and treat the ticket as coordination context linked to an authoritative AegisOps record. |
| Endpoint evidence | Endpoint evidence, host facts, agent state, file paths, process data, or local collector status is presented as AegisOps evidence or source truth without reviewed custody, parser, and record linkage. | Reject the shortcut and require an AegisOps evidence record with custody and scope binding. |
| Network evidence | Network evidence, flow state, packet metadata, proxy logs, Suricata output, or external telemetry is presented as AegisOps evidence or source truth without reviewed custody, parser, and record linkage. | Reject the shortcut and require an AegisOps evidence record with custody and scope binding. |
| Evidence systems | External evidence-system status, retention, export, report, or custody text is presented as AegisOps evidence, release, gate, or production truth without explicit binding to the AegisOps evidence record. | Reject the shortcut and repair or refuse the projection instead of redefining truth around the external system. |
| Browser state | Browser URL, route state, local storage, session storage, cookie state, DOM text, or client navigation state is presented as AegisOps workflow truth. | Reject the shortcut and reload or recalculate from authoritative AegisOps records. |
| UI cache | Client cache, optimistic update, badge, counter, detail DTO, projection, or stale refresh result is presented as AegisOps workflow truth. | Reject the shortcut and repair the derived surface from authoritative AegisOps records. |
| Downstream receipts | Downstream receipt, webhook acknowledgement, adapter response, export receipt, support bundle receipt, or delivery receipt is presented as AegisOps reconciliation or closeout truth without AegisOps reconciliation. | Reject the shortcut and require the AegisOps reconciliation record or mismatch path. |
| Demo data | Seed data, sample fixture, demo persona, synthetic event, example receipt, fake secret, TODO value, or placeholder credential is presented as production truth. | Reject the shortcut and require trusted production binding, real credential custody, or an explicit demo-only refusal. |

## 4. Later-Issue Citation Rule

Any later issue that adds breadth for AI, Wazuh, Shuffle, tickets, endpoint evidence, network evidence, external evidence systems, browser state, UI cache, downstream receipts, or demo data must cite this policy and name the exact negative-test class it preserves.

Expected citation examples:

- Phase 54 Wazuh signal intake must cite this policy for Wazuh status shortcut rejection and explicit AegisOps admission linkage.
- Phase 57 AI advisory trace must cite this policy for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.
- Phase 59 delegated execution must cite this policy for Shuffle workflow-success shortcut rejection and AegisOps receipt linkage.
- Phase 60 reconciliation must cite this policy for downstream receipt shortcut rejection and durable reconciliation linkage.
- Phase 62 report export and Phase 63 support bundle work must cite this policy when derived reports, exports, bundles, or external evidence systems are present.
- Phase 66 RC and Phase 67 GA evidence packets must cite this policy when gate evidence includes browser state, UI cache, downstream receipts, demo data, tickets, Wazuh, Shuffle, AI, endpoint evidence, network evidence, or external evidence-system context.

## 5. Forbidden Shortcuts

Forbidden shortcuts include:

- using AI recommendation text as approval, execution, reconciliation, case closure, detector activation, or source truth;
- using Wazuh alert status to close, reconcile, release, or gate an AegisOps record;
- using Shuffle workflow success to close, reconcile, release, or gate an AegisOps record;
- using ticket status to close, approve, reconcile, release, or gate an AegisOps record;
- using endpoint or network telemetry as authoritative evidence without reviewed custody, parser, scope, and AegisOps evidence-record linkage;
- using browser state, UI cache, optimistic updates, badges, counters, or detail projections as workflow truth;
- using downstream receipts without AegisOps reconciliation linkage as closeout truth;
- using demo data, placeholders, fake secrets, TODO values, or sample credentials as production truth.

## 6. Validation

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/test-verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1047 --config <supervisor-config-path>`.

The verifier must fail when any subordinate surface listed in this policy is missing, when later-issue citation rules are missing, when AI approval, AI execution, AI reconciliation, AI case closure, AI detector activation, or AI source-truth shortcuts are allowed, when Wazuh or Shuffle state is allowed to close or reconcile AegisOps records, or when publishable guidance uses workstation-local absolute paths.

## 7. Non-Goals

- No runtime behavior changes are approved by this policy.
- No broad AI, Wazuh, Shuffle, ticket, evidence, browser, UI, downstream receipt, demo-data, SIEM, SOAR, installer, release, or production behavior is implemented here.
- No subordinate surface becomes approval, execution, reconciliation, case closure, source truth, gate truth, or production truth.
- No derived surface may redefine AegisOps workflow truth when it drifts from the authoritative record chain.
