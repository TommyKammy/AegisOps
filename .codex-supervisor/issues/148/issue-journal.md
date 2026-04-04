# Issue #148: implementation: tighten reviewed rule readiness gates and split Sigma field semantics

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/148
- Branch: codex/issue-148
- Workspace: .
- Journal: .codex-supervisor/issues/148/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: aef666ce40fdc7d1ff4d577ff8f1097412f23274
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-04T03:37:42.573Z

## Latest Codex Summary
- Tightened the readiness-gate verifiers first to reproduce the gap, then updated the source onboarding contract, Sigma translation strategy, detection lifecycle framework, Sigma metadata template, and reviewed Windows Phase 6 Sigma rules to split field semantics into `match_required`, `triage_required`, `activation_gating`, and `confidence_degrading`.
- Focused verifier tests now pass, along with the issue-specified document verification commands and the curated Sigma slice verifier.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The current repo still encoded ambiguous `field_dependencies` semantics and allowed `schema-reviewed` wording to blur staging translation readiness with production activation readiness.
- What changed: Tightened the doc/template/rule verifiers and tests first, reproduced the failure against the old fixtures, then updated the governed docs and reviewed Windows Sigma rules to make staging translation gates explicit and reserve production activation for `detection-ready` activation-gating dependencies.
- Current blocker: none
- Next exact step: Commit the verified documentation and Sigma contract changes on `codex/issue-148`.
- Verification gap: Did not run unrelated broader repository verification beyond the focused doc/template/rule checks for this issue.
- Files touched: docs/source-onboarding-contract.md; docs/sigma-to-opensearch-translation-strategy.md; docs/detection-lifecycle-and-rule-qa-framework.md; docs/phase-6-opensearch-detector-artifact-validation.md; docs/source-families/windows-security-and-endpoint/onboarding-package.md; sigma/aegisops-sigma-metadata-template.yml; sigma/curated/windows-security-and-endpoint/*.yml; scripts/verify-*.sh; scripts/test-verify-*.sh
- Rollback concern: Low; changes are documentation and verification only, but the curated-slice verifier now enforces field-semantics structure rather than exact file hashes.
- Last focused command: bash scripts/verify-source-onboarding-contract-doc.sh && bash scripts/verify-sigma-to-opensearch-translation-strategy-doc.sh && bash scripts/verify-detection-lifecycle-and-rule-qa-framework.sh && bash scripts/verify-sigma-metadata-template.sh
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
