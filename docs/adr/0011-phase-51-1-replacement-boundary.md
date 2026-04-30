# ADR-0011: Phase 51.1 SMB SecOps Replacement Boundary

- **Status**: Accepted
- **Date**: 2026-04-30
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`, `docs/adr/0002-wazuh-shuffle-control-plane-thesis.md`
- **Product**: AegisOps
- **Related Issues**: #1041, #1042
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

ADR-0002 defines AegisOps as a governed SecOps decision and execution control plane above Wazuh and Shuffle. Phase 51 needs sharper replacement wording so README positioning and follow-on materials can say what AegisOps replaces without weakening that authority boundary.

The risk is two-sided:

- under-claiming leaves SMB buyers and operators with no clear operating-experience replacement story; and
- over-claiming makes AegisOps sound like it reimplements Wazuh, Shuffle, or every SIEM/SOAR capability.

This ADR fixes the product-language boundary only. It does not change runtime behavior, substrate integrations, approval policy, reconciliation policy, packaging, release state, or general availability scope.

## 2. Decision

AegisOps replaces the SMB SecOps operating experience, not Wazuh internals, Shuffle internals, or every SIEM and SOAR capability.

Replacement means the reviewed operator experience for daily SMB SOC work: Wazuh detects, AegisOps decides, records, and reconciles, and Shuffle executes reviewed delegated routine work.

The replacement boundary is the working surface and record chain used by an SMB security operator to review signals, manage alerts and cases, attach evidence, approve actions, delegate routine execution, reconcile results, audit the work, and prove release readiness.

AegisOps must not use replacement language to claim control over detection engines, correlation internals, workflow-engine internals, or unimplemented breadth.

## 3. Allowed Replacement Claims

- Allowed claim: AegisOps can replace the daily SMB SOC operating experience above Wazuh and Shuffle.
- Allowed claim: AegisOps can replace ad hoc ticket-and-script coordination with authoritative alert, case, approval, action request, receipt, reconciliation, audit, and release records.
- Allowed claim: AegisOps can provide a governed SIEM/SOAR operating layer for SMB teams when Wazuh and Shuffle provide the reviewed substrate capabilities.

The allowed wording may describe an SMB SOC/SIEM/SOAR replacement experience only when the sentence keeps Wazuh and Shuffle in their substrate roles and keeps AegisOps records as workflow truth.

## 4. Disallowed Replacement Claims

- Disallowed claim: AegisOps already replaces every SIEM capability.
- Disallowed claim: AegisOps already replaces every SOAR capability.
- Disallowed claim: AegisOps reimplements Wazuh detection internals.
- Disallowed claim: AegisOps reimplements Shuffle workflow internals.

The disallowed wording also includes claims that AegisOps makes external substrate state authoritative, that the assistant can operate as an autonomous SOC, or that pilot artifacts imply release-candidate or general-availability breadth.

## 5. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, and release truth.

AI must not approve actions, execute actions, reconcile execution, close cases, activate detectors, or become source truth.

Wazuh alert status is not AegisOps case truth.

Shuffle workflow success is not AegisOps reconciliation truth.

Tickets, evidence systems, browser state, UI cache, downstream receipts, demo data, Wazuh, Shuffle, and AI output remain subordinate context.

This ADR rejects any shortcut that promotes subordinate surfaces into AegisOps workflow truth.

Derived summaries, status badges, projections, dashboards, detail DTOs, operator-facing text, and downstream receipts must be recalculated from or linked back to authoritative AegisOps records. If they drift, the projection must be repaired; the authoritative record chain must not be redefined around the projection.

## 6. Substrate Responsibilities

Wazuh is the detection substrate.

Shuffle is the routine automation substrate.

Wazuh may detect, classify, and expose upstream security signal state. AegisOps must admit that signal through reviewed intake and explicit linkage before it becomes AegisOps alert, case, evidence, audit, release, or reconciliation truth.

Shuffle may execute reviewed delegated routine work. AegisOps must record action intent, approval, delegation, execution receipt, reconciliation, and mismatch handling as its own authoritative workflow records.

Future substrate changes may replace Wazuh or Shuffle only through a later accepted ADR or scoped implementation issue. A substrate change must not change the replacement boundary by implication.

## 7. Implementation Impact

This ADR does not implement CLI behavior, Wazuh profile generation, Shuffle profile generation, AI daily operations, SIEM breadth, SOAR breadth, packaging, release-candidate behavior, or general-availability behavior.

Phase 51.2 may update README positioning against this ADR, but it must preserve this boundary: AegisOps replaces the SMB SecOps operating experience above Wazuh and Shuffle, not their internals or every SIEM/SOAR capability.

Follow-on docs may cite this ADR when they need allowed replacement wording, disallowed replacement wording, or authority-boundary language for product positioning.

## 8. Security Impact

The security posture is unchanged by this documentation contract. The ADR narrows language that could otherwise become unsafe implementation pressure.

Approval, execution, reconciliation, case closure, detector activation, source truth, and release truth remain explicit AegisOps control-plane responsibilities. External products and AI assistance remain untrusted or subordinate until admitted through the reviewed boundary that owns the authoritative record.

This ADR reinforces fail-closed review: missing, malformed, or partial signals from AI, Wazuh, Shuffle, tickets, evidence systems, browser state, UI cache, downstream receipts, or demo data must not be promoted into workflow truth.

## 9. Rollback / Exit Strategy

Rollback is required if replacement wording causes reviewers or operators to treat AegisOps as a reimplementation of Wazuh, Shuffle, or every SIEM/SOAR capability.

The rollback path is to supersede this ADR with a narrower accepted ADR and remove README or roadmap language that cites the broader replacement boundary.

Rollback does not require runtime migration because this ADR does not change runtime behavior or write durable records.

## 10. Validation

Run `bash scripts/verify-phase-51-1-replacement-boundary-adr.sh`.

Run `bash scripts/test-verify-phase-51-1-replacement-boundary-adr.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1042 --config <supervisor-config-path>`.

The verifier must fail when allowed or disallowed claim wording is missing, when the ADR claims AegisOps already replaces every SIEM/SOAR capability, or when the ADR promotes AI, Wazuh, Shuffle, tickets, evidence systems, browser state, UI cache, downstream receipts, or demo data into authority.

## 11. Non-Goals

- No runtime behavior changes are approved by this ADR.
- No CLI, Wazuh profile generation, Shuffle profile generation, AI daily operations, SIEM breadth, SOAR breadth, packaging, release-candidate, or general-availability behavior is implemented or approved.
- No Wazuh internals, Shuffle internals, detector engine behavior, workflow engine behavior, ticket behavior, evidence-system behavior, browser behavior, UI cache behavior, downstream receipt behavior, or demo-data behavior becomes authoritative workflow truth.
- No AI approval, AI execution, AI reconciliation, AI case closure, AI detector activation, or AI source-truth authority is approved.
- No Wazuh alert status becomes case truth.
- No Shuffle workflow success becomes reconciliation truth.

## 12. Approval

- **Proposed By**: Codex for Issue #1042
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-30
