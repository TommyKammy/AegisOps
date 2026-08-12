# ADR 0020: Phase 67 GA-Prerequisite Boundary

- **Status**: Accepted
- **Date**: 2026-08-12
- **Owners**: AegisOps maintainers
- **Related Issues**: #1414, #1418
- **Supersedes**: Positive statements that equate Phase 67 completion with GA acceptance

## Context

The Phase 51.3 gate contract originally mapped Phase 67 directly to GA. The
materialized Phase 67 Epic instead defines a bounded, single-host,
non-production real-integration trial that explicitly excludes GA acceptance,
production rollout, design-partner success, HA, scale, and disaster recovery.

That mismatch makes a closed issue, merged pull request, passing verifier, or
successful lab component trial appear capable of accepting GA even though the
required real-user, production-operability, supportability, and limitation
evidence does not exist.

## Decision

Phase 66 remains the bounded RC evidence phase.

Phase 67 performs bounded GA-prerequisite validation. It may collect real Wazuh
and Shuffle interoperability evidence and publish owned blockers, but it does
not accept GA, authorize production rollout, or establish customer success.

GA acceptance is a separate gate decision. It requires all RC evidence plus
revision-bound real-user or design-partner evidence across the intended launch
scope, production-operability evidence, support and upgrade ownership, and
explicit disposition of every blocking limitation. A human approver who is
independent of evidence production must make the decision.

A Phase 67 result such as
`integration_trial_passed_with_owned_limitations` remains prerequisite evidence
only. Issue closure, pull-request merge, CI success, external-service health, or
a subordinate Wazuh or Shuffle result cannot convert it into GA acceptance.

## Consequences

- Phase 67 issues may be materialized before all GA evidence exists so that
  missing evidence can be observed and assigned, but their verdicts must remain
  bounded and non-production.
- The Phase 67 Epic must remain open while its current-revision trial or owned
  prerequisite blockers remain incomplete.
- A later GA gate must name its real-user or design-partner record, environment,
  operator, support owner, upgrade owner, accepted limitations, independent
  human approver, and decision.
- Existing documentation and verifiers must reject positive claims that Phase
  67 itself is GA or that completing Phase 67 accepts GA.

## Non-Goals

- This decision does not accept the GA gate.
- This decision does not prove production readiness or customer success.
- This decision does not weaken the Phase 51.3 GA evidence requirements.
