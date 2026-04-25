# GitHub Audit Wazuh-Backed Source Profile Onboarding Package

## 1. Family Scope and Readiness State

Readiness state: `detection-ready`

The approved Phase 14 source family is GitHub audit.

This package documents the reviewed Wazuh-backed source profile for GitHub audit alerts entering AegisOps as vendor-neutral analytic signals.

Reviewed detection-ready scope: GitHub audit records admitted through the reviewed Wazuh-backed intake boundary for repository and organization privilege, access, and workflow-administration review signals.

It preserves accountable source identity, actor identity, target identity, repository or organization context, privilege-change metadata, workflow-administration metadata, timestamp quality, and Wazuh provenance in the shared control-plane language.

Future detection content may reference GitHub audit only for repository and organization privilege, access, and workflow-administration review signals that preserve accountable source identity, actor identity, target identity, repository or organization context, privilege-change or workflow-administration metadata, timestamp quality, and Wazuh provenance.

This package does not approve live GitHub API actioning, response automation, source-side credentials, GitHub-owned case authority, direct vendor workflow truth, non-audit GitHub telemetry families, or detector activation without separate detector review.

This package does not approve live GitHub API actioning, response automation, source-side credentials, or non-audit GitHub telemetry families.

## 2. Parser Ownership and Lifecycle Boundary

Parser ownership remains with IT Operations, Information Systems Department.

The parser implementation boundary is the reviewed Wazuh intake handling that preserves the GitHub audit signal shape, accountable source identity, actor identity, target identity, repository or organization context, privilege-change metadata, workflow-administration metadata, timestamp quality, and Wazuh provenance.

## 3. Parser and Version Evidence

Reviewed parser evidence source: Wazuh `github_audit` decoder evidence represented by `decoder.name`, Wazuh rule metadata, the reviewed `github-audit-alert.json` fixture, and the parser ownership boundary in this package.

Reviewed parser version evidence: the approved detection-ready scope is pinned to the documented Wazuh-backed fixture shape and the `github_audit` decoder identity until a separately reviewed parser package introduces a stronger semantic version. Parser or decoder changes that alter source field names, timestamp semantics, identity mapping, repository mapping, or provenance mapping must refresh this package before detector dependencies can rely on the changed shape.

This parser/version evidence is sufficient for the bounded detection-ready scope above. It is not approval for broad parser rollout, live source enrollment, direct GitHub collection, or non-audit telemetry expansion.

## 4. Raw Payload References

Representative raw payload references are stored in `control-plane/tests/fixtures/wazuh/`.

The reviewed success-path reference in this package covers a GitHub repository privilege-change record. It is the current parser/version evidence anchor for the approved detection-ready scope.

Raw payload reference set:

| File | Scenario | Notes |
| ---- | ---- | ---- |
| `github-audit-alert.json` | GitHub repository privilege change | Synthetic Wazuh alert shaped after a GitHub audit record; preserves accountable source identity, actor identity, target identity, repository and organization context, and privilege-change metadata. |

All raw payload references in this package are synthetic review artifacts. They exist to anchor mapping review, replay validation, parser/version evidence, and detector-use scope review, not to stand in for production enrollment evidence.

## 5. Normalization Mapping Summary

| Source-native evidence | Normalized target | Review status | Notes |
| ---- | ---- | ---- | ---- |
| `manager.name`, `agent.id` when present | `source.accountable_source_identity` | Required | Wazuh remains the reviewed intake boundary, and the accountable source identity must stay explicit. |
| `data.actor.*` | `identity.actor` | Required | Actor identity remains reviewable for triage and recommendation. |
| `data.target.*` | `identity.target` | Required | Target identity remains reviewable when the audit event names a user, team, role, or other impacted object. |
| `data.organization.*`, `data.repository.*` | `asset.organization`, `asset.repository` | Required | Repository or organization context remains explicit and vendor-neutral. |
| `data.privilege.*`, `data.audit_action` | `privilege.*` and `provenance.audit_action` | Required | Privilege-change metadata remains reviewable without turning the control plane into a GitHub API client. |
| Workflow-administration action metadata when present in `data.audit_action` and related `data.*` fields | `provenance.audit_action` and reviewed event context | Required within approved scope | Workflow-administration signals are detection-ready only when the action, actor, target, repository or organization, timestamp, and Wazuh provenance remain explicit. |
| `rule.id`, `rule.level`, `rule.description`, `decoder.name`, `location`, `timestamp` | `provenance.*`, `@timestamp`, `event.created` | Required | Native Wazuh provenance and source event time remain preserved for later review and reconciliation. |

## 6. Field Coverage Verification

| Semantic area | Coverage status | Evidence or exception path |
| ---- | ---- | ---- |
| Accountable source identity | Required | Preserved through `manager.name` in the reviewed Wazuh alert and surfaced as `source.accountable_source_identity`. |
| Actor identity | Required | Preserved through `data.actor.*` and mapped into `identity.actor`. |
| Target identity | Required | Preserved through `data.target.*` and mapped into `identity.target`. |
| Repository or organization context | Required | Preserved through `data.organization.*` and `data.repository.*` and mapped into `asset.*`. |
| Privilege-change metadata | Required | Preserved through `data.privilege.*` and `data.audit_action`. |
| Workflow-administration metadata | Required within approved scope | Detection-ready only when `data.audit_action` and related GitHub audit fields preserve the reviewed workflow-administration event, actor, target, repository or organization, timestamp, and provenance context. |
| Timestamp quality | Required | Preserved through the Wazuh alert `timestamp`; collector-created and ingest-arrival timestamps require separate runtime evidence before detector activation can treat them as activation-gating fields. |
| Parser version traceability | Required | Anchored to the reviewed Wazuh `github_audit` decoder identity, Wazuh rule metadata, and the `github-audit-alert.json` fixture shape until a versioned parser package supersedes it. |
| Direct GitHub API actioning | Prohibited non-goal | Not part of the reviewed source profile or control-plane intake behavior. |
| GitHub-owned case or workflow truth | Prohibited non-goal | AegisOps remains the authoritative control plane for case state, approval state, action state, and reconciliation. |
| Non-audit GitHub telemetry families | Unavailable | This package only reviews the GitHub audit family. Non-audit source families require separate onboarding before detection content can depend on them. |

No required baseline coverage is intentionally deferred for the approved detection-ready scope. Any detector that needs fields outside the rows above remains blocked until the onboarding package documents a reviewed exception path or a separate source-family package.

## 7. Provenance Evidence

Provenance Evidence: GitHub audit records remain detection-ready only when the Wazuh intake boundary preserves `rule.id`, `rule.level`, `rule.description`, `decoder.name`, `location`, `timestamp`, `manager.name`, and the GitHub audit `data.request_id` or equivalent source request context when present.

The reviewed fixture preserves Wazuh manager identity, decoder identity, rule identity, rule severity, rule description, source location, event timestamp, source family, GitHub audit action, actor, target, organization, repository, privilege metadata, and request context.

AegisOps treats those fields as source evidence for review and detector prerequisites. They do not make GitHub the authority for AegisOps case state, approval state, response state, or reconciliation outcomes.

If accountable source identity, actor identity, target identity, repository or organization context, timestamp quality, parser evidence, or Wazuh provenance is missing or malformed, the event is outside the approved detection-ready scope unless a future reviewed exception path explicitly states otherwise.

## 8. Replay Fixture Plan

Replay fixtures are represented by `control-plane/tests/fixtures/wazuh/github-audit-alert.json`.

The reviewed fixture is sufficient for future parser and mapping validation without claiming that live source onboarding is approved.

The fixture also anchors the current detector-use approval package by proving the source family can preserve identity, repository context, privilege context, timestamp, and provenance evidence for the bounded GitHub audit scope.

## 9. Detector-Use Approval and Limits

Detector-Use Approval and Limits: GitHub audit is approved as a detection-ready source family only for future detection content whose source prerequisites fit the reviewed repository and organization audit scope documented here.

Detector activation still requires separate rule review, rollout review, and Wazuh rule lifecycle validation.

The only currently documented activation candidate for this package is `docs/source-families/github-audit/detector-activation-candidates/repository-admin-membership-change.md`.

Approved detector-use prerequisites:

- source family is GitHub audit through the Wazuh-backed intake boundary;
- detector fields are limited to the reviewed field coverage and provenance evidence in this package;
- the detector records false-positive expectations and analyst handling notes from the GitHub audit triage runbook;
- production activation is separately reviewed under the detection lifecycle and Wazuh rule lifecycle documents; and
- any missing prerequisite signal blocks detector-ready handling rather than being inferred from repository names, path shape, comments, or nearby metadata.

Blocked detector-use paths:

- direct GitHub API actioning or source-side mutation;
- GitHub-owned case authority, approval state, action state, or workflow truth;
- non-audit GitHub telemetry families;
- detectors that need GitHub fields outside the reviewed coverage table without an explicit exception path;
- detector activation without separate detector review; and
- treating placeholder, malformed, or missing provenance as valid detector evidence.

## 10. Known Gaps and Non-Goals

This package is detection-ready only for the reviewed GitHub audit scope above. It does not claim unlimited GitHub audit coverage, broad GitHub telemetry coverage, source credential readiness, live enrollment approval, direct GitHub actioning, response automation, or production detector activation.

The current review package does not introduce live source enrollment, credentials, parser rollout beyond the reviewed Wazuh-backed boundary, direct GitHub API actioning, response automation, GitHub-owned workflow truth, or any telemetry family beyond GitHub audit.
