# Phase 65.6 Default SMB Documentation Pack

- **Status**: Accepted as the Phase 65 default SMB documentation pack contract for beta/design-partner packaging review only.
- **Date**: 2026-06-07
- **Owner**: AegisOps maintainers
- **Related Issues**: #1378, #1379, #1385
- **Related Baseline**: `docs/phase-65-1-release-bundle-inventory.md`, `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, `docs/phase-58-5-upgrade-rollback-plan-contract.md`, `docs/phase-58-6-support-bundle-redaction-contract.md`

This contract defines the default SMB documentation pack that Phase 65 beta/design-partner release packaging may carry as product-facing guidance.

The documentation pack is packaging evidence and operator guidance only. It does not implement runtime installer behavior, support bundle generation, live backup, live restore, live upgrade, live rollback, migration execution, beta evidence templates, RC gate acceptance, GA readiness, production support readiness, or self-service commercial readiness.

## 1. Pack Identifier And Manifest

The documentation pack identifier is `phase-65-default-smb-docs-pack-v1`.

The structured manifest template is `docs/deployment/release/phase-65-6-default-smb-docs-pack.yaml`.

Every maintained Phase 65 SMB documentation pack record must include:

- documentation pack identifier `phase-65-default-smb-docs-pack-v1`;
- Phase 65.1 inventory identifier `phase-65-release-bundle-inventory-v1`;
- pack owner;
- reviewed date;
- beta/design-partner scope;
- topic coverage for installation, daily operation, source onboarding, automation catalog, AI usage, backup and restore, support bundle, upgrade, and rollback;
- repo-relative primary reference for every topic;
- verifier output reference for `bash scripts/verify-phase-65-6-default-smb-docs-pack.sh`;
- explicit boundary that docs are guidance and packaging evidence only; and
- quoted approval record `"issue #1385"`.

Docs pack records must use repo-relative paths, documented env vars, and placeholders such as `<repository-revision>`, `<release-bundle-dir>`, `<evidence-dir>`, `<runtime-env-file>`, `<support-bundle.md>`, `<upgrade-plan.md>`, `<rollback-plan.md>`, `<codex-supervisor-root>`, and `<supervisor-config-path>`.

## 2. Required Topic Coverage

| Topic | Primary reference | Supporting reference | Required boundary |
| --- | --- | --- | --- |
| Installation | `docs/phase-65-2-offline-install-bundle-contract.md` | `docs/deployment/first-user-stack.md` | Installation docs are beta/design-partner guidance and do not prove clean-host success, RC readiness, GA readiness, or production installer completeness. |
| Daily operation | `docs/runbook.md` | `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md` | Daily operation docs guide operator workflow and do not become workflow truth, support truth, release truth, or gate truth. |
| Source onboarding | `docs/source-onboarding-contract.md` | `docs/phase-61-minimum-source-catalog-contract.md` | Source onboarding docs do not approve live source enrollment, parser deployment, credentials, detector activation, or production source readiness. |
| Automation catalog | `docs/phase-62-reviewed-automation-catalog-contract.md` | `docs/phase-62-5-manual-fallback-contract.md` | Automation docs describe reviewed delegated actions only and do not approve direct Shuffle launch, execution truth, reconciliation truth, or protected-target mutation. |
| AI usage | `docs/phase-59-3-ai-trace-lifecycle-contract.md` | `docs/phase-59-4-ai-disabled-degraded-mode-contract.md` | AI usage docs preserve advisory-only posture and do not grant AI approval, execution, reconciliation, case closure, release, gate, or readiness authority. |
| Backup and restore | `docs/phase-58-3-backup-command-contract.md` | `docs/phase-58-4-restore-dry-run-contract.md` | Backup and restore docs are planning and rehearsal guidance only and do not prove live backup success, live restore success, RC readiness, or GA readiness. |
| Support bundle | `docs/phase-58-6-support-bundle-redaction-contract.md` | `docs/deployment/operator-training-handoff-packet.md` | Support bundle docs require redaction and do not grant support operator authority, production support readiness, workflow truth, release truth, or gate truth. |
| Upgrade and rollback | `docs/phase-58-5-upgrade-rollback-plan-contract.md` | `docs/phase-65-3-release-channel-upgrade-manifest-contract.md` | Upgrade and rollback docs are reviewed planning evidence only and do not run upgrades, run rollbacks, satisfy RC gates, satisfy GA gates, or prove release readiness. |

## 3. Beta Documentation Boundaries

The pack is intentionally assembled from reviewed, repo-owned documents instead of ad hoc operator notes. It gives beta/design-partner users a navigable product-facing index while preserving the source contracts that own runtime, support, release, and authority boundaries.

The pack must not include workstation-local absolute paths, production secrets, placeholder credentials treated as valid auth, customer-private examples, private support text, raw alerts, raw logs, raw tickets, screenshots, or unredacted support bundle output.

Migration guidance remains a dedicated Phase 65.7 issue. Beta known-limitations and design-partner evidence templates remain a dedicated Phase 65.8 issue. This pack may link to those future surfaces once they exist, but it must not implement them or claim them complete.

## 4. Authority Boundary

Documentation, manifest entries, screenshots, examples, generated indexes, verifier output, issue-lint output, release notes, support notes, AI text, ticket text, browser state, UI cache, Wazuh state, Shuffle state, and operator-facing summaries are subordinate guidance or packaging evidence only.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, workflow, and closeout truth.

The documentation pack cannot approve live installation, source onboarding, automation execution, AI decisions, backup success, restore success, support readiness, upgrade success, rollback success, Beta gate acceptance, RC gate acceptance, GA gate acceptance, production support readiness, self-service commercial readiness, or commercial replacement readiness.

## 5. Verification

Run the focused docs pack verifier:

```sh
bash scripts/verify-phase-65-6-default-smb-docs-pack.sh
```

Run the verifier self-test:

```sh
bash scripts/test-verify-phase-65-6-default-smb-docs-pack.sh
```

Run inherited checks:

```sh
bash scripts/verify-phase-58-6-support-bundle-redaction-contract.sh
bash scripts/verify-publishable-path-hygiene.sh
```

Run issue-lint:

```sh
node <codex-supervisor-root>/dist/index.js issue-lint 1385 --config <supervisor-config-path>
```

The verifier must reject missing install docs, missing daily-ops docs, missing source-onboarding docs, missing automation docs, missing AI-usage docs, missing backup/restore docs, missing support-bundle docs, missing upgrade/rollback docs, workstation-local paths, secrets, customer-private examples, inferred RC pass, inferred GA pass, production support readiness claims, and self-service commercial readiness claims.

## 6. Non-Claims

This documentation pack does not claim first-user RC success, support-bundle completion for RC, production support readiness, Phase 66 RC readiness, Phase 67 GA readiness, Beta gate acceptance, RC gate acceptance, GA gate acceptance, self-service commercial readiness, commercial replacement readiness, live install success, live backup success, live restore success, live upgrade success, live rollback success, migration completion, beta evidence template completion, production entitlement enforcement, billing readiness, or hosted update-service readiness.

This documentation pack is beta/design-partner documentation packaging evidence only. It is not workflow authority, support authority, runtime execution authority, release gate authority, Beta gate authority, RC gate authority, GA gate authority, entitlement authority, billing authority, verifier truth, issue-lint truth, documentation truth, support truth, readiness truth, or substitute evidence for the Phase 51.3 gate contract.
