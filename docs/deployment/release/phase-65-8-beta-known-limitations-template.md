# Phase 65.8 Beta Known-Limitations Template

- **Status**: Accepted as a Phase 65 beta/design-partner template only.
- **Date**: 2026-06-07
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1386
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-64-1-reviewed-limitation-ownership-records.md`, `docs/phase-64-5-phase66-limitation-handoff.md`, `docs/phase-64-closeout-evaluation.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`

This template captures known limitations for a beta/design-partner packaging handoff.

The template is planning and evidence-capture scaffolding only. It does not collect real beta evidence, resolve limitations, complete support-bundle evidence, assemble an RC packet, accept RC gates, collect GA evidence, prove GA readiness, or claim commercial replacement readiness.

## 1. Template Header

| Field | Value |
| --- | --- |
| Template identifier | `phase-65-8-beta-known-limitations-template-v1` |
| Release bundle identifier | `<phase-65-release-bundle-identifier>` |
| Template owner | `<named-owner>` |
| Review date | `<YYYY-MM-DD>` |
| Next review date | `<YYYY-MM-DD>` |
| Limitation source | `docs/phase-64-1-reviewed-limitation-ownership-records.md` |
| Phase 64 limitation handoff reference | `docs/phase-64-5-phase66-limitation-handoff.md` |
| Phase 66 RC proof boundary | `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md` |
| Support-bundle posture | `<not-complete|tracked-separately|blocked-with-owner>` |
| Upgrade posture | `<not-reviewed|reviewed-planning-only|blocked-with-owner>` |
| Template authority boundary | `planning-and-evidence-capture-scaffold-only` |

## 2. Known Limitation Register

Every row must name an owner, review date, limitation reference, evidence reference, blocker disposition, accepted risk posture, support-bundle posture, upgrade posture, and next review date.

| Limitation ID | Owner | Review date | Limitation reference | Evidence references | Blocker disposition | Accepted risk posture | Support-bundle posture | Upgrade posture | Next review date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<limitation-id>` | `<named-owner>` | `<YYYY-MM-DD>` | `docs/phase-64-1-reviewed-limitation-ownership-records.md#<limitation-anchor>` | `<repo-relative-evidence-reference>` | `<blocking|accepted-with-owner|tracked-separately|not-reviewed>` | `<bounded-pre-rc-risk|requires-follow-up|not-reviewed>` | `<not-complete|tracked-separately|blocked-with-owner>` | `<not-reviewed|reviewed-planning-only|blocked-with-owner>` | `<YYYY-MM-DD>` |

## 3. Blocker Disposition Rules

- `blocking` means the beta/design-partner handoff must not proceed until a reviewed owner and follow-up are recorded.
- `accepted-with-owner` means the limitation remains explicit and owned; it does not become resolved limitation truth.
- `tracked-separately` means the supporting evidence remains outside this template and must cite the owning record.
- `not-reviewed` blocks readiness interpretation until review is complete.

Support-bundle posture must remain explicit because support-bundle completion is excluded from this template. Upgrade posture must remain explicit because upgrade evidence remains planning evidence unless later gate records prove it independently.

## 4. Authority Boundary

Beta known-limitations templates are planning and evidence-capture scaffolds only. They do not become limitation truth, support truth, release truth, gate truth, readiness truth, RC proof, GA proof, or commercial replacement truth by themselves.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

Phase 64 limitation records and Phase 64.5 Phase 66 handoff evidence remain subordinate limitation ownership inputs. Phase 66 must still prove RC gates independently under the Phase 51.3 gate contract.

Verifier output and issue-lint output are validation and metadata evidence only. They do not become readiness truth, release truth, gate truth, limitation truth, support truth, or RC proof.

## 5. Validation

Run:

```sh
bash scripts/verify-phase-65-8-beta-evidence-templates.sh
bash scripts/test-verify-phase-65-8-beta-evidence-templates.sh
bash scripts/verify-phase-64-5-phase66-limitation-handoff.sh
bash scripts/verify-publishable-path-hygiene.sh
node <codex-supervisor-root>/dist/index.js issue-lint 1386 --config <supervisor-config-path>
```

## 6. Non-Claims

This beta known-limitations template does not claim real beta launch evidence, real design-partner evidence, support-bundle completion, limitation resolution, RC readiness, RC gate acceptance, GA readiness, GA gate acceptance, production support readiness, self-service commercial readiness, or commercial replacement readiness.

This template is not workflow authority, support authority, release authority, gate authority, limitation truth, readiness truth, RC proof, GA proof, verifier truth, issue-lint truth, or substitute evidence for the Phase 51.3 gate contract.
