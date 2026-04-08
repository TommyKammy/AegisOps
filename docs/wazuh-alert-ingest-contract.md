# Wazuh Alert Ingest Contract

## 1. Purpose

This document defines the reviewed Wazuh-specific intake contract for alerts entering the AegisOps control-plane boundary.

It supplements `docs/secops-domain-model.md` and `docs/control-plane-state-model.md` by making the Wazuh-native alert shape, identifier mapping, provenance expectations, and downstream linkage rules explicit for future Phase 12 adapter work.

This contract defines reviewed data-shape and ownership expectations only. It does not approve live adapter code, queue behavior, case-routing policy, or broader source-family expansion.

## 2. Boundary and Ownership

Wazuh remains the owner of the Wazuh-native alert record that it emits.

AegisOps admits that Wazuh-native record through the intake boundary as one `Substrate Detection Record` and one vendor-neutral `Analytic Signal` candidate.

The admitted analytic signal remains distinct from the downstream `Alert`, `Case`, and `Evidence` records that AegisOps may create later.

The ownership split is:

| Record or identifier | Owner | Boundary note |
| ---- | ---- | ---- |
| Wazuh-native alert payload | Wazuh | Preserves Wazuh-specific structure, rule metadata, agent metadata, and native record semantics. |
| `substrate_detection_record_id` | AegisOps intake boundary with durable linkage back to Wazuh | Namespaced durable reference to the originating Wazuh-native alert record. |
| `analytic_signal_id` | AegisOps | Identifier for the admitted vendor-neutral `Analytic Signal` created or updated from the Wazuh-origin input. |
| `alert_id` | AegisOps | Identifier for analyst-facing alert work created from the analytic signal when routing policy decides tracked work is required. |
| `case_id` | AegisOps | Identifier for durable investigation state when alert work is promoted into a case or opened directly from analytic intake. |
| `evidence_id` and provenance records | AegisOps | Evidence custody and derivation links that preserve how Wazuh source material informed later analyst work. |

Neither the Wazuh-native alert identifier nor the admitted `analytic_signal_id` may be reused as an `alert_id` or `case_id`.

## 3. Reviewed Wazuh Input Contract

The intake boundary accepts one Wazuh alert JSON object at a time.

Wazuh documentation examples show stable top-level alert fields including `id`, `timestamp`, `rule`, `agent`, `manager`, `decoder`, `location`, and source-specific `data` payload sections. The contract below narrows which of those fields are required at the AegisOps boundary and which remain optional but preservable source context.

### 3.1 Required Fields

The following fields are required for a Wazuh alert to cross the AegisOps intake boundary:

| Wazuh field | Required expectation | AegisOps mapping |
| ---- | ---- | ---- |
| `id` | Non-empty string. Unique only within Wazuh semantics and must be preserved exactly as emitted. | Source value for the Wazuh-native identifier and the suffix used to form `substrate_detection_record_id`. |
| `timestamp` | Timezone-qualified event-emission timestamp string that can be parsed into an aware datetime. | Canonical upstream alert timestamp preserved in provenance and used as the baseline admitted-signal observation time. |
| `rule.id` | Non-empty rule identifier string. | Preserved as native rule provenance and available to derive or review routing and correlation context. |
| `rule.level` | Integer severity value as emitted by Wazuh. | Preserved as native severity provenance; it does not become an AegisOps lifecycle state by itself. |
| `rule.description` | Non-empty descriptive string. | Preserved as human-readable native claim context for the admitted signal. |
| `agent.id` or equivalent manager-local source identity for manager-origin alerts | At least one accountable source identity must exist. | Preserved in provenance and used in the bounded correlation input set. |
| Raw alert payload | Full JSON object as received. | Preserved as source material for evidence and later review; intake normalization must not destroy the original Wazuh-native shape. |

### 3.2 Optional Fields

The following fields are optional at the intake boundary but must be preserved when present:

| Wazuh field | Optional expectation | AegisOps handling |
| ---- | ---- | ---- |
| `agent.name` | Human-readable endpoint or source name. | Preserve as source context only. |
| `agent.ip` | Source endpoint IP address. | Preserve as source context only. |
| `manager.name` | Wazuh manager identity. | Preserve as provenance context showing which Wazuh control point emitted the record. |
| `decoder.name` | Decoder family or parser name. | Preserve as native parsing provenance. |
| `location` | Wazuh event location string. | Preserve as native routing and provenance context. |
| `rule.groups` | Native Wazuh grouping tags. | Preserve as classification context; do not treat them as AegisOps queue state. |
| `rule.mitre.*` | Native ATT&CK metadata when present. | Preserve as source analytic context. |
| `data.*` | Source-family-specific structured payload. | Preserve as source evidence context and optional analytic enrichment input. |
| Additional top-level fields | Any extra Wazuh-native fields present in a reviewed alert shape. | Preserve losslessly unless a separate reviewed contract forbids them. |

## 4. Identifier Mapping

The intake boundary must preserve the distinction between Wazuh-native identifiers, admitted analytic-signal identifiers, and downstream control-plane workflow identifiers.

| Concern | Mapping rule |
| ---- | ---- |
| Wazuh-native record identity | Preserve Wazuh `id` exactly as the native alert identifier. |
| `substrate_detection_record_id` | Set to `wazuh:<id>` unless the input is already namespaced as `wazuh:<id>`. This matches the shipped control-plane rule that substrate detection identifiers are namespaced by substrate key. |
| `analytic_signal_id` | AegisOps-minted durable identifier for the admitted signal. It may be supplied by the intake adapter or deterministically derived by AegisOps from correlation context, but it remains an AegisOps-owned identifier rather than a Wazuh-native field. |
| `alert_id` | AegisOps-minted analyst-work identifier created only if routing policy decides analyst queueing or tracked alert handling is required. |
| `case_id` | AegisOps-minted investigation identifier created only when durable investigation tracking is required. |

`substrate_detection_record_id`, `analytic_signal_id`, `alert_id`, and `case_id` are related references, not interchangeable lifecycle keys.

## 5. Timestamp Mapping

Wazuh `timestamp` is the required upstream record timestamp and must remain preserved in provenance.

The admitted signal must populate its first-seen or last-seen timing from reviewed upstream timestamps rather than from when an analyst later opens an alert or case.

When later intake logic distinguishes first observation from restatement or update time, it must preserve that distinction without rewriting the original Wazuh-native timestamp.

## 6. Routing and Correlation Inputs

The Wazuh alert contract does not define final analyst-queue behavior, but it does define the minimum native context that the `Analytic Signal` admission step must preserve for later routing and deduplication decisions.

The admitted signal must preserve:

- the namespaced `substrate_detection_record_id`;
- the AegisOps `analytic_signal_id`;
- the Wazuh-native severity and rule provenance from `rule.id`, `rule.level`, and `rule.description`;
- accountable source identity from `agent.id` or the reviewed manager-local equivalent;
- reviewed timing from Wazuh `timestamp`; and
- enough preserved source context to explain why later alert or case routing happened.

The current reviewed Wazuh correlation boundary uses the following native fields in addition to `rule.id` and accountable source identity:

- `location`
- `data.srcip`
- `data.srcuser`
- `data.integration`
- `data.event_type`
- `data.source_family`
- `data.audit_action`
- `data.privilege.change_type`
- `data.privilege.scope`
- `data.privilege.permission`
- `data.privilege.role`

Those fields may separate distinct incidents during deduplication or restatement decisions, but they still remain reviewed correlation inputs rather than lifecycle identifiers.

The following preserved native fields remain provenance-only context in the shipped adapter and must not change alert lineage by themselves:

- `rule.level`
- `rule.description`
- `rule.groups`
- `rule.mitre.*`
- `agent.name`
- `agent.ip`
- `manager.name` beyond its accountable-source role when no agent identity is present
- `decoder.name`
- additional `data.*` fields outside the reviewed correlation allowlist above

## 7. Provenance Expectations

Every admitted Wazuh-origin `Analytic Signal` must preserve provenance sufficient to answer all of the following:

- which exact Wazuh-native alert record was admitted;
- which Wazuh manager or source context emitted it;
- which Wazuh rule metadata described the native claim;
- what native timestamp Wazuh attached to the alert; and
- which later AegisOps alert, case, evidence, and reconciliation records were linked to that admitted signal.

The minimum provenance set for Wazuh-origin intake is:

| Provenance element | Minimum expectation |
| ---- | ---- |
| Native payload preservation | Retain the original Wazuh-native JSON payload as source material or evidence input. |
| Source system marker | Preserve that the record originated from the `wazuh` detection substrate. |
| Native identifier linkage | Preserve Wazuh `id` and the namespaced `substrate_detection_record_id`. |
| Native timing | Preserve Wazuh `timestamp` and any later AegisOps ingest or comparison timestamps separately. |
| Rule provenance | Preserve `rule.id`, `rule.level`, and `rule.description`; keep optional `rule.groups` and `rule.mitre.*` when present. |
| Source provenance | Preserve `agent.*`, `manager.*`, `decoder.name`, and `location` when present. |

## 8. Mapping into Analytic Signal and Downstream Records

One Wazuh-native alert admission produces or updates one first-class `Analytic Signal` record, not a case by default.

The reviewed mapping is:

| Wazuh-origin input | AegisOps record or field | Mapping expectation |
| ---- | ---- | ---- |
| One Wazuh alert JSON object | `Substrate Detection Record` | The raw Wazuh-native record remains the upstream source fact. |
| Wazuh `id` | `substrate_detection_record_id` | Namespaced durable linkage as `wazuh:<id>`. |
| Wazuh `timestamp` | `Analytic Signal.first_seen_at` and `Analytic Signal.last_seen_at` baseline | Used as the upstream observation time unless later reviewed logic proves a restatement or update window. |
| Wazuh rule and source context | `Analytic Signal` provenance and correlation context | Preserved without converting native fields into AegisOps workflow state. |
| Admitted signal requiring analyst work | `alert_id` linkage on the analytic signal and alert record | AegisOps may create or update an `Alert` while keeping the `Analytic Signal` first-class and separately addressable. |
| Alert promotion or direct investigation intake | `case_id` linkage | A case may link back to either the alert, the analytic signal, or both as defined in the control-plane state model. |
| Preserved raw payload and source metadata | `Evidence` and reconciliation linkage | Later evidence and reconciliation records must point back to the Wazuh-origin signal chain rather than rewriting provenance into notes. |

Downstream alert and case lifecycle state must remain AegisOps-owned even when the native Wazuh record is restated, updated, or disappears from the substrate view.

The reviewed Wazuh case-promotion path must create or update the durable `CaseRecord` when reviewed alert handling moves an alert into `escalated_to_case`; later Wazuh restatements must preserve that promoted `case_id` linkage rather than depending on a manually prelinked case created outside the ingest and review path.

## 9. Non-Goals

This contract does not:

- implement a live Wazuh adapter;
- define the exact algorithm for `analytic_signal_id` generation;
- approve concrete analyst-queue behavior;
- expand the contract to all future detection substrates; or
- redefine the control-plane ownership rules already established in `docs/control-plane-state-model.md`.
