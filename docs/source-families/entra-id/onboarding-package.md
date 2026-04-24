# Entra ID Wazuh-Backed Source Profile Onboarding Package

## 1. Family Scope and Readiness State

Readiness state: `detection-ready`

The approved Phase 14 source family is Entra ID.

This package documents the reviewed Wazuh-backed source profile for Entra ID alerts entering AegisOps as vendor-neutral analytic signals.

Phase 34 selects Entra ID as the second detection-ready family because it already has the clearer reviewed multi-source evidence path from the approved Entra ID case-admission slice.

Reviewed detection-ready scope: Entra ID audit records admitted through the reviewed Wazuh-backed intake boundary for tenant, directory, authentication, and privilege-change review signals.

It preserves tenant context, actor identity, target identity, authentication context, privilege-change metadata, and directory provenance in the shared control-plane language.

Future detection content may reference Entra ID only for tenant, directory, authentication, and privilege-change review signals that preserve accountable source identity, actor identity, target identity, timestamp quality, and Wazuh provenance.

This package does not approve direct Entra ID actioning, directory changes, credential changes, source-side credentials, Entra ID-owned case authority, non-audit Entra ID telemetry families, or detector activation without separate detector review.

This package does not approve direct Entra ID actioning, non-audit Entra ID telemetry families, source-side credentials, or runtime automation.

## 2. Parser Ownership and Lifecycle Boundary

Parser ownership remains with IT Operations, Information Systems Department.

The parser implementation boundary is the reviewed Wazuh intake handling that preserves Entra ID tenant context, actor identity, target identity, authentication context, privilege metadata, timestamp quality, and directory provenance.

## 3. Parser and Version Evidence

Reviewed parser evidence source: Wazuh `entra_id` decoder evidence represented by `decoder.name`, Wazuh rule metadata, the reviewed `entra-id-alert.json` fixture, the Phase 25 reviewed Entra ID case-admission slice, and the parser ownership boundary in this package.

Reviewed parser version evidence: the approved detection-ready scope is pinned to the documented Wazuh-backed fixture shape and the `entra_id` decoder identity until a separately reviewed parser package introduces a stronger semantic version. Parser or decoder changes that alter source field names, timestamp semantics, identity mapping, tenant mapping, directory-object mapping, or provenance mapping must refresh this package before detector dependencies can rely on the changed shape.

This parser/version evidence is sufficient for the bounded detection-ready scope above. It is not approval for broad parser rollout, live source enrollment, direct Entra ID collection, or non-audit telemetry expansion.

## 4. Raw Payload References

Representative raw payload references are stored in `control-plane/tests/fixtures/wazuh/`.

The reviewed success-path reference in this package covers an Entra ID privileged role assignment record. It is the current parser/version evidence anchor for the approved detection-ready scope.

Raw payload reference set:

| File | Scenario | Notes |
| ---- | ---- | ---- |
| `entra-id-alert.json` | Entra ID privileged role assignment | Synthetic Wazuh alert shaped after an Entra ID audit record; preserves tenant context, actor identity, target identity, authentication context, directory provenance, and privilege-change metadata. |

All raw payload references in this package are synthetic review artifacts. They exist to anchor mapping review, replay validation, parser/version evidence, and detector-use scope review, not to stand in for production enrollment evidence.

## 5. Normalization Mapping Summary

| Source-native evidence | Normalized target | Review status | Notes |
| ---- | ---- | ---- | ---- |
| `manager.name`, `agent.id` when present | `source.accountable_source_identity` | Required | Wazuh remains the reviewed intake boundary, and the accountable source identity must stay explicit. |
| `data.actor.*` | `identity.actor` | Required | Actor identity remains reviewable for triage and recommendation. |
| `data.target.*` | `identity.target` | Required | Target identity remains reviewable when the audit event names a user, group, role assignment, app registration, credential object, or policy object. |
| `data.tenant.*` | `asset.tenant` | Required | Tenant context remains explicit and vendor-neutral. |
| `data.app.*` | `asset.app` | Required | App or service-principal context remains explicit without collapsing it into a source-local vendor label. |
| `data.authentication.*` | `authentication.*` | Required | Authentication context remains reviewable without implying direct directory enforcement. |
| `data.privilege.*`, `data.audit_action`, `data.correlation_id`, `data.operation`, `data.record_type` | `privilege.*` and `provenance.*` | Required | Privilege-change metadata, correlation identifiers, and directory provenance remain reviewable without turning the control plane into an Entra ID API client. |
| `rule.id`, `rule.level`, `rule.description`, `decoder.name`, `location`, `timestamp` | `provenance.*`, `@timestamp`, `event.created` | Required | Native Wazuh provenance and source event time remain preserved for later review and reconciliation. |

## 6. Field Coverage Verification

| Semantic area | Coverage status | Evidence or exception path |
| ---- | ---- | ---- |
| Accountable source identity | Required | Preserved through `manager.name` in the reviewed Wazuh alert and surfaced as `source.accountable_source_identity`. |
| Tenant context and directory boundary | Required | Preserved through `data.tenant.*` in the reviewed fixture. |
| Actor identity and target identity | Required | Preserved through `data.actor.*` and `data.target.*` and mapped into `identity.*`. |
| Authentication context | Required | Preserved through `data.authentication.*` and mapped into `authentication.*`. |
| App context | Required | Preserved through `data.app.*` and mapped into `asset.app`. |
| Privilege-change metadata | Required | Preserved through `data.privilege.*`, `data.audit_action`, and `data.operation`. |
| Timestamp quality | Required | Preserved through the Wazuh alert `timestamp`; collector-created and ingest-arrival timestamps require separate runtime evidence before detector activation can treat them as activation-gating fields. |
| Parser version traceability | Required | Anchored to the reviewed Wazuh `entra_id` decoder identity, Wazuh rule metadata, and the `entra-id-alert.json` fixture shape until a versioned parser package supersedes it. |
| Direct Entra ID actioning | Prohibited non-goal | Not part of the reviewed source profile or control-plane intake behavior. |
| Entra ID-owned case or workflow truth | Prohibited non-goal | AegisOps remains the authoritative control plane for case state, approval state, action state, and reconciliation. |
| Non-audit Entra ID telemetry families | Unavailable | This package only reviews the Entra ID audit family. Non-audit source families require separate onboarding before detection content can depend on them. |

No required baseline coverage is intentionally deferred for the approved detection-ready scope. Any detector that needs fields outside the rows above remains blocked until the onboarding package documents a reviewed exception path or a separate source-family package.

## 7. Provenance Evidence

Provenance Evidence: Entra ID records remain detection-ready only when the Wazuh intake boundary preserves `rule.id`, `rule.level`, `rule.description`, `decoder.name`, `location`, `timestamp`, `manager.name`, and the Entra ID `data.request_id` or `data.correlation_id` source request context when present.

The reviewed fixture preserves Wazuh manager identity, decoder identity, rule identity, rule severity, rule description, source location, event timestamp, source family, Entra ID audit action, actor, target, tenant, app or service-principal context, authentication context, privilege metadata, correlation id, and request context.

AegisOps treats those fields as source evidence for review and detector prerequisites. They do not make Entra ID the authority for AegisOps case state, approval state, response state, or reconciliation outcomes.

If accountable source identity, actor identity, target identity, tenant context, timestamp quality, parser evidence, or Wazuh provenance is missing or malformed, the event is outside the approved detection-ready scope unless a future reviewed exception path explicitly states otherwise.

## 8. Replay Fixture Plan

Replay fixtures are represented by `control-plane/tests/fixtures/wazuh/entra-id-alert.json`.

The reviewed fixture is sufficient for future parser and mapping validation without claiming that live source onboarding is approved.

The fixture also anchors the current detector-use approval package by proving the source family can preserve tenant context, actor identity, target identity, authentication context, privilege context, timestamp, and provenance evidence for the bounded Entra ID scope.

## 9. Detector-Use Approval and Limits

Detector-Use Approval and Limits: Entra ID is approved as a detection-ready source family only for future detection content whose source prerequisites fit the reviewed tenant, directory, authentication, and privilege-change audit scope documented here.

Detector activation still requires separate rule review, rollout review, and Wazuh rule lifecycle validation.

Approved detector-use prerequisites:

- source family is Entra ID through the Wazuh-backed intake boundary;
- detector fields are limited to the reviewed field coverage and provenance evidence in this package;
- the detector records false-positive expectations and analyst handling notes from the Entra ID triage runbook;
- production activation is separately reviewed under the detection lifecycle and Wazuh rule lifecycle documents; and
- any missing prerequisite signal blocks detector-ready handling rather than being inferred from tenant names, directory object names, comments, or nearby metadata.

Blocked detector-use paths:

- direct Entra ID actioning or source-side mutation;
- Entra ID-owned case authority, approval state, action state, or workflow truth;
- non-audit Entra ID telemetry families;
- detectors that need Entra ID fields outside the reviewed coverage table without an explicit exception path;
- detector activation without separate detector review; and
- treating placeholder, malformed, or missing provenance as valid detector evidence.

## 10. Known Gaps and Non-Goals

This package is detection-ready only for the reviewed Entra ID scope above. It does not claim unlimited Entra ID coverage, broad Microsoft cloud telemetry coverage, source credential readiness, live enrollment approval, direct Entra ID actioning, response automation, or production detector activation.

The current review package does not introduce live source enrollment, credentials, parser rollout beyond the reviewed Wazuh-backed boundary, direct Entra ID actioning, response automation, Entra ID-owned workflow truth, or any telemetry family beyond Entra ID audit.
