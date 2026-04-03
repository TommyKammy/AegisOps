# Windows Security and Endpoint Telemetry Onboarding Package

## 1. Family Scope and Readiness State

Readiness state: `schema-reviewed`

The selected telemetry family for the Phase 6 slice is Windows security and endpoint telemetry.

This package documents the reviewed onboarding evidence for Windows Security Event Log and closely related endpoint security records that preserve host identity, actor or target identity when present, source provenance, and event timing semantics for the initial Phase 6 use cases.

This package does not approve live source enrollment, credential onboarding, parser deployment, or detector activation.

## 2. Parser Ownership and Lifecycle Boundary

Parser ownership remains with IT Operations, Information Systems Department.

The parser implementation boundary for this family is the ingest-side handling that preserves Windows event channel, provider, event identifier, host identity, actor or target identity fields when present, and AegisOps provenance annotations needed for later replay validation.

Versioned parser changes remain future implementation work. Until a parser exists, this package treats the replay fixtures and mapping notes as the review baseline that future parser work must satisfy.

## 3. Raw Payload References

Representative raw payload references are stored under `ingest/replay/windows-security-and-endpoint/raw/`.

The reviewed success-path references in this package cover privileged group membership change, audit log cleared, and new local user created records.

The reviewed edge-case references in this package cover missing actor identity and forwarded-event timestamp caveats.

Raw payload reference set:

| File | Scenario | Notes |
| ---- | ---- | ---- |
| `privileged-group-addition.json` | Local Administrators membership change | Synthetic event shaped after Windows Event ID `4732`; preserves actor, target, host, channel, and provider context. |
| `audit-log-cleared.json` | Security audit log cleared | Synthetic event shaped after Windows Event ID `1102`; preserves actor, host, and event channel provenance. |
| `local-user-created.json` | Local user account created | Synthetic event shaped after Windows Event ID `4720`; preserves actor and target account context. |
| `local-user-created-missing-actor.json` | Local user created with missing subject identity | Edge case for source records where actor identity is absent or redacted and the parser must preserve the gap explicitly. |
| `audit-log-cleared-forwarded-time-anomaly.json` | Forwarded audit-log-cleared event with timestamp caveat | Edge case for forwarded-event timing where source event time and collector receipt time diverge materially. |

All raw payload references in this package are synthetic or redacted review artifacts. They exist to anchor mapping review and replay validation, not to stand in for production enrollment evidence.

## 4. Normalization Mapping Summary

The mapping summary below aligns the reviewed Windows references to the canonical telemetry schema baseline and the family-specific Windows coverage requirements.

| Source-native evidence | Normalized target | Review status | Notes |
| ---- | ---- | ---- | ---- |
| `System.EventID`, `System.Channel`, `System.Provider.Name`, `EventData.OperationType` | `event.code`, `event.category`, `event.type`, `event.action`, `event.provider`, `event.module`, `event.dataset` | Required | Event classification and Windows provenance are preserved for all reviewed records. |
| `System.TimeCreated`, collector receipt metadata | `@timestamp`, `event.created`, `event.ingested` | Required | Forwarded-event timing caveats are captured in the edge fixture set rather than hidden. |
| `Computer`, collector host notes | `host.name`, `host.hostname`, `related.hosts` | Required | Host identity remains required baseline coverage for the family. |
| `EventData.SubjectUserName`, `EventData.SubjectDomainName`, `EventData.SubjectUserSid` | `user.name`, `user.domain`, `user.id`, `related.user` | Required when present | Missing-actor cases remain explicit gaps and are not fabricated. |
| `EventData.MemberName`, `EventData.TargetUserName`, `EventData.TargetSid`, `EventData.GroupName` | `destination.user.name`, `destination.user.id`, `group.name`, `related.user` | Required when present | Target identity is preserved for the selected administrative-account use cases. |
| Collector path and parser revision marker | `aegisops.provenance.ingest_path`, `aegisops.provenance.parser_version`, `event.original` | Required | Provenance stays reviewable even before live parser code exists. |

Shared required field groups remain required under `docs/canonical-telemetry-schema-baseline.md`, and this package does not reinterpret missing source values as optional.

## 5. Replay Fixture Plan

Replay fixtures are stored under `ingest/replay/windows-security-and-endpoint/normalized/`.

The `success.ndjson` corpus contains one representative normalized record for each initial Phase 6 Windows use case:

- privileged group membership change;
- audit log cleared; and
- new local user created.

The `edge.ndjson` corpus contains reviewed edge cases that future parser validation must preserve explicitly:

- a missing-actor record that keeps the target identity and provenance but marks the absent actor context as a reviewed gap; and
- a forwarded-event timing case that preserves source time, collector-created time, ingest time, and the known timing caveat under AegisOps provenance.

The raw and normalized fixtures together are sufficient for future parser and mapping validation without claiming that the family is already detection-ready.

## 6. Known Gaps and Non-Goals

This package remains `schema-reviewed` rather than `detection-ready` because parser version evidence, field-by-field coverage sign-off across a broader Windows event range, and explicit detector-use approval remain future work.

The current review package does not introduce live source enrollment, credentials, parser rollout, or detector deployment.

Known reviewed gaps:

- Process lineage, token or integrity detail coverage, and remote-network context are not yet represented in this narrow fixture set.
- The missing-actor edge case remains a detection-readiness blocker for detections that require authoritative actor attribution.
- Forwarded-event timing caveats require explicit parser handling before timestamp-sensitive detections can rely on those records.

Non-goals for this issue:

- live Windows collector onboarding;
- production parser or ingest pipeline implementation;
- rule activation or detector rollout; and
- any telemetry family beyond Windows security and endpoint telemetry.
