# AegisOps Phase 62.5 Manual Fallback Contract

This contract extends the accepted Phase 54.8 Shuffle manual fallback posture to every reviewed Phase 62 default catalog action. It covers unavailable Shuffle, rejected execution, missing receipt, stale receipt, mismatched receipt, and missing operator-note paths for `enrichment_only_lookup`, `operator_notification`, `manual_escalation_request`, and `create_tracking_ticket`.

## Contract

Every reviewed Phase 62 action must have a manual fallback requirement with explicit fallback owner, operator note, affected action, blocked or unavailable reason, expected evidence, and follow-up posture. The required fallback states are `shuffle_unavailable`, `execution_rejected`, `missing_receipt`, `stale_receipt`, and `mismatched_receipt`.

Manual fallback is subordinate operator guidance. It cannot bypass approval, prove execution, substitute for a bound AegisOps execution receipt, become reconciliation truth, close cases, close tickets, or claim readiness.

## Validation Rules

Phase 62.5 validation must fail closed when:

- a reviewed Phase 62 action is missing a manual fallback requirement;
- fallback owner, operator note, affected action, blocked reason, expected evidence, follow-up posture, or fallback state is missing or blank;
- fallback state is outside `shuffle_unavailable`, `execution_rejected`, `missing_receipt`, `stale_receipt`, and `mismatched_receipt`;
- fallback affected action does not match the reviewed catalog action;
- an operator note bypasses approval, proves execution, or becomes reconciliation truth;
- expected evidence promotes Shuffle workflow state, ticket state, UI cache, browser state, AI output, verifier output, issue-lint output, or an operator note to AegisOps truth;
- follow-up posture reports successful execution, completion, reconciliation, case closure, ticket closure, Beta, RC, GA, or commercial replacement readiness; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented environment variables, or placeholders such as `<supervisor-config-path>` and `<codex-supervisor-root>`.

## Validation

Run `bash scripts/verify-phase-62-5-manual-fallback-contract.sh`.

Run `PYTHONPATH=control-plane:control-plane/tests python3 -m unittest control-plane.tests.test_phase62_action_policy_registry`.

Run `bash scripts/verify-phase-54-8-manual-fallback-contract.sh`.

Run `bash scripts/verify-phase-54-9-shuffle-authority-boundary-negative-tests.sh`.

Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1319 --config <supervisor-config-path>`.

## Non-Goals

No Controlled Write or Hard Write default enablement, autonomous remediation, destructive response, protected-target mutation, approval bypass, execution-proof shortcut, reconciliation shortcut, direct workflow launch, broad SOAR marketplace expansion, production secret material, customer-private data, Phase 63 evidence expansion, Phase 66 RC proof, Beta readiness, RC readiness, GA readiness, commercial replacement readiness, or broad SOAR replacement readiness is implemented here.
