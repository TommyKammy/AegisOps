# Microsoft 365 Audit Wazuh-Backed Source Profile Onboarding Package

## 1. Family Scope and Readiness State

Readiness state: `schema-reviewed`

The approved Phase 14 source family is Microsoft 365 audit.

This package documents the reviewed Wazuh-backed source profile for Microsoft 365 audit alerts entering AegisOps as vendor-neutral analytic signals.

It preserves tenant context, actor identity, target identity, authentication context, privilege-change metadata, and workload provenance in the shared control-plane language.

This package does not approve direct Microsoft 365 actioning, non-audit Microsoft 365 telemetry families, source-side credentials, or runtime automation.

## 2. Parser Ownership and Lifecycle Boundary

Parser ownership remains with IT Operations, Information Systems Department.

The parser implementation boundary is the reviewed Wazuh intake handling that preserves Microsoft 365 audit tenant context, actor identity, target identity, authentication context, privilege metadata, and workload provenance.

Versioned parser changes remain future implementation work. Until a parser exists, this package treats the reviewed fixture and mapping notes as the review baseline that future parser work must satisfy.

## 3. Raw Payload References

Representative raw payload references are stored in `control-plane/tests/fixtures/wazuh/`.

The reviewed success-path reference in this package covers a Microsoft 365 mailbox permission change record.

Raw payload reference set:

| File | Scenario | Notes |
| ---- | ---- | ---- |
| `microsoft-365-audit-alert.json` | Microsoft 365 mailbox permission change | Synthetic Wazuh alert shaped after a Microsoft 365 audit record; preserves tenant context, actor identity, target identity, authentication context, workload provenance, and privilege-change metadata. |

All raw payload references in this package are synthetic review artifacts. They exist to anchor mapping review and replay validation, not to stand in for production enrollment evidence.

## 4. Normalization Mapping Summary

| Source-native evidence | Normalized target | Review status | Notes |
| ---- | ---- | ---- | ---- |
| `manager.name`, `agent.id` when present | `source.accountable_source_identity` | Required | Wazuh remains the reviewed intake boundary, and the accountable source identity must stay explicit. |
| `data.actor.*` | `identity.actor` | Required | Actor identity remains reviewable for triage and recommendation. |
| `data.target.*` | `identity.target` | Required | Target identity remains reviewable when the audit event names a mailbox, site, document, team, policy, or message object. |
| `data.tenant.*` | `asset.tenant` | Required | Tenant context remains explicit and vendor-neutral. |
| `data.app.*` | `asset.app` | Required | App or workload context remains explicit without collapsing it into a source-local vendor label. |
| `data.authentication.*` | `authentication.*` | Required | Authentication context remains reviewable without implying direct sign-in enforcement. |
| `data.privilege.*`, `data.audit_action`, `data.workload`, `data.operation`, `data.record_type` | `privilege.*` and `provenance.*` | Required | Privilege-change metadata and workload provenance remain reviewable without turning the control plane into a Microsoft 365 API client. |
| `rule.id`, `rule.level`, `rule.description`, `decoder.name`, `location`, `timestamp` | `provenance.*` | Required | Native Wazuh provenance remains preserved for later review and reconciliation. |

## 5. Field Coverage Verification

| Semantic area | Coverage status | Evidence or exception path |
| ---- | ---- | ---- |
| Tenant context and workload boundary | Required | Preserved through `data.tenant.*` and `data.workload` in the reviewed fixture. |
| Actor identity and target identity | Required | Preserved through `data.actor.*` and `data.target.*` and mapped into `identity.*`. |
| Authentication context | Required | Preserved through `data.authentication.*` and mapped into `authentication.*`. |
| App context | Required | Preserved through `data.app.*` and mapped into `asset.app`. |
| Privilege-change metadata | Required | Preserved through `data.privilege.*`, `data.audit_action`, and `data.operation`. |
| Direct Microsoft 365 actioning | Intentionally deferred | Not part of the reviewed source profile or control-plane intake behavior. |
| Non-audit Microsoft 365 telemetry families | Unavailable | This package only reviews the Microsoft 365 audit family. |

## 6. Replay Fixture Plan

Replay fixtures are represented by `control-plane/tests/fixtures/wazuh/microsoft-365-audit-alert.json`.

The reviewed fixture is sufficient for future parser and mapping validation without claiming that live source onboarding is approved.

## 7. Known Gaps and Non-Goals

This package remains `schema-reviewed` rather than `detection-ready` because parser version evidence, broader Microsoft 365 audit field coverage, and explicit detector-use approval remain future work.

The current review package does not introduce live source enrollment, credentials, parser rollout, direct Microsoft 365 actioning, runtime automation, or any telemetry family beyond Microsoft 365 audit.
