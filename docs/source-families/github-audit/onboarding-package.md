# GitHub Audit Wazuh-Backed Source Profile Onboarding Package

## 1. Family Scope and Readiness State

Readiness state: `schema-reviewed`

The approved Phase 14 source family is GitHub audit.

This package documents the reviewed Wazuh-backed source profile for GitHub audit alerts entering AegisOps as vendor-neutral analytic signals.

It preserves accountable source identity, actor identity, target identity, repository or organization context, and privilege-change metadata in the shared control-plane language.

This package does not approve live GitHub API actioning, response automation, source-side credentials, or non-audit GitHub telemetry families.

## 2. Parser Ownership and Lifecycle Boundary

Parser ownership remains with IT Operations, Information Systems Department.

The parser implementation boundary is the reviewed Wazuh intake handling that preserves the GitHub audit signal shape, accountable source identity, actor identity, target identity, repository or organization context, and privilege-change metadata.

Versioned parser changes remain future implementation work. Until a parser exists, this package treats the reviewed fixture and mapping notes as the review baseline that future parser work must satisfy.

## 3. Raw Payload References

Representative raw payload references are stored in `control-plane/tests/fixtures/wazuh/`.

The reviewed success-path reference in this package covers a GitHub repository privilege-change record.

Raw payload reference set:

| File | Scenario | Notes |
| ---- | ---- | ---- |
| `github-audit-alert.json` | GitHub repository privilege change | Synthetic Wazuh alert shaped after a GitHub audit record; preserves accountable source identity, actor identity, target identity, repository and organization context, and privilege-change metadata. |

All raw payload references in this package are synthetic review artifacts. They exist to anchor mapping review and replay validation, not to stand in for production enrollment evidence.

## 4. Normalization Mapping Summary

| Source-native evidence | Normalized target | Review status | Notes |
| ---- | ---- | ---- | ---- |
| `manager.name`, `agent.id` when present | `source.accountable_source_identity` | Required | Wazuh remains the reviewed intake boundary, and the accountable source identity must stay explicit. |
| `data.actor.*` | `identity.actor` | Required | Actor identity remains reviewable for triage and recommendation. |
| `data.target.*` | `identity.target` | Required | Target identity remains reviewable when the audit event names a user, team, role, or other impacted object. |
| `data.organization.*`, `data.repository.*` | `asset.organization`, `asset.repository` | Required | Repository or organization context remains explicit and vendor-neutral. |
| `data.privilege.*`, `data.audit_action` | `privilege.*` and `provenance.audit_action` | Required | Privilege-change metadata remains reviewable without turning the control plane into a GitHub API client. |
| `rule.id`, `rule.level`, `rule.description`, `decoder.name`, `location`, `timestamp` | `provenance.*` | Required | Native Wazuh provenance remains preserved for later review and reconciliation. |

## 5. Field Coverage Verification

| Semantic area | Coverage status | Evidence or exception path |
| ---- | ---- | ---- |
| Accountable source identity | Required | Preserved through `manager.name` in the reviewed Wazuh alert and surfaced as `source.accountable_source_identity`. |
| Actor identity | Required | Preserved through `data.actor.*` and mapped into `identity.actor`. |
| Target identity | Required | Preserved through `data.target.*` and mapped into `identity.target`. |
| Repository or organization context | Required | Preserved through `data.organization.*` and `data.repository.*` and mapped into `asset.*`. |
| Privilege-change metadata | Required | Preserved through `data.privilege.*` and `data.audit_action`. |
| Direct GitHub API actioning | Intentionally deferred | Not part of the reviewed source profile or control-plane intake behavior. |
| Non-audit GitHub telemetry families | Unavailable | This package only reviews the GitHub audit family. |

## 6. Replay Fixture Plan

Replay fixtures are represented by `control-plane/tests/fixtures/wazuh/github-audit-alert.json`.

The reviewed fixture is sufficient for future parser and mapping validation without claiming that live source onboarding is approved.

## 7. Known Gaps and Non-Goals

This package remains `schema-reviewed` rather than `detection-ready` because parser version evidence, broader GitHub audit field coverage, and explicit detector-use approval remain future work.

The current review package does not introduce live source enrollment, credentials, parser rollout, direct GitHub API actioning, response automation, or any telemetry family beyond GitHub audit.
