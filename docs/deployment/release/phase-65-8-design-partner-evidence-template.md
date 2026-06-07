# Phase 65.8 Design-Partner Evidence Template

- **Status**: Accepted as a Phase 65 beta/design-partner template only.
- **Date**: 2026-06-07
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1386
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-64-1-reviewed-limitation-ownership-records.md`, `docs/phase-64-5-phase66-limitation-handoff.md`, `docs/phase-64-closeout-evaluation.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`

This template captures the fields a future design-partner evidence packet must provide before any beta/design-partner handoff can be reviewed.

The template is planning and evidence-capture scaffolding only. It does not collect real design-partner evidence, conduct user interviews, resolve limitations, complete support-bundle evidence, assemble an RC packet, accept RC gates, collect GA evidence, prove GA readiness, or claim commercial replacement readiness.

## 1. Template Header

| Field | Value |
| --- | --- |
| Template identifier | `phase-65-8-design-partner-evidence-template-v1` |
| Release bundle identifier | `<phase-65-release-bundle-identifier>` |
| Template owner | `<named-owner>` |
| Review date | `<YYYY-MM-DD>` |
| Next review date | `<YYYY-MM-DD>` |
| Design-partner scope | `<redacted-design-partner-scope-or-not-collected>` |
| Limitation source | `docs/phase-64-1-reviewed-limitation-ownership-records.md` |
| Phase 64 limitation handoff reference | `docs/phase-64-5-phase66-limitation-handoff.md` |
| Phase 66 RC proof boundary | `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md` |
| Support-bundle posture | `<not-complete|tracked-separately|blocked-with-owner>` |
| Upgrade posture | `<not-reviewed|reviewed-planning-only|blocked-with-owner>` |
| Template authority boundary | `planning-and-evidence-capture-scaffold-only` |

## 2. Design-Partner Evidence Register

Every row must name an owner, review date, design-partner evidence reference, limitation reference, evidence reference, blocker disposition, accepted risk posture, support-bundle posture, upgrade posture, and next review date.

| Evidence area | Owner | Review date | Design-partner evidence reference | Limitation reference | Evidence references | Blocker disposition | Accepted risk posture | Support-bundle posture | Upgrade posture | Next review date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<install|wazuh-signal|shuffle-execution|ai-trace|report-export|restore|upgrade|support-bundle|limitations>` | `<named-owner>` | `<YYYY-MM-DD>` | `<not-collected|repo-relative-redacted-evidence-reference>` | `docs/phase-64-1-reviewed-limitation-ownership-records.md#<limitation-anchor>` | `<repo-relative-evidence-reference>` | `<blocking|accepted-with-owner|tracked-separately|not-reviewed>` | `<bounded-pre-rc-risk|requires-follow-up|not-reviewed>` | `<not-complete|tracked-separately|blocked-with-owner>` | `<not-reviewed|reviewed-planning-only|blocked-with-owner>` | `<YYYY-MM-DD>` |

## 3. Evidence Capture Rules

- `not-collected` is valid only as an explicit beta/design-partner evidence gap with owner, blocker disposition, accepted risk posture, and next review date.
- Redacted evidence references must be repo-relative or reviewed record references; raw customer data, private interview notes, live credentials, screenshots with private data, and workstation-local paths are not valid template content.
- Blocker disposition must remain explicit and cannot be inferred from owner assignment, evidence file presence, issue closure, verifier success, or issue-lint success.
- Support-bundle posture and upgrade posture must remain explicit because neither support-bundle completion nor upgrade proof is completed by this template.

## 4. Authority Boundary

Design-partner evidence templates are planning and evidence-capture scaffolds only. They do not become design-partner truth, limitation truth, support truth, release truth, gate truth, readiness truth, RC proof, GA proof, or commercial replacement truth by themselves.

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

This design-partner evidence template does not claim real beta launch evidence, real design-partner evidence collection, support-bundle completion, limitation resolution, RC readiness, RC gate acceptance, GA readiness, GA gate acceptance, production support readiness, self-service commercial readiness, or commercial replacement readiness.

This template is not workflow authority, support authority, release authority, gate authority, design-partner truth, limitation truth, readiness truth, RC proof, GA proof, verifier truth, issue-lint truth, or substitute evidence for the Phase 51.3 gate contract.
