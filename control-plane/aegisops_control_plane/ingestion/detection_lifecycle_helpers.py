from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hmac
import logging
from typing import TYPE_CHECKING, Callable, Mapping
import uuid

from ..adapters.wazuh import WazuhAlertAdapter
from ..models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AnalyticSignalRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    FindingAlertIngestResult,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    LifecycleTransitionRecord,
    NativeDetectionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from ..reviewed_slice_policy import REVIEWED_LIVE_SOURCE_FAMILIES

if TYPE_CHECKING:
    from .detection_lifecycle import DetectionIntakeService
    from ..service import AegisOpsControlPlaneService


LATEST_LIFECYCLE_TRANSITION_UNSET = object()
_LINKED_ALERT_CASE_LIFECYCLE_LOCK_FAMILY = "linked_alert_case_lifecycle"
_SAME_TIMESTAMP_LIFECYCLE_TRANSITION_ID_PREFIX = "~"


class DetectionLifecycleTransitionHelper:
    def __init__(self, service: AegisOpsControlPlaneService) -> None:
        self._service = service

    def lock_lifecycle_transition_subject(
        self,
        record_family: str,
        record_id: str,
    ) -> None:
        lock_subject = getattr(
            self._service._store,
            "lock_lifecycle_transition_subject",
            None,
        )
        if callable(lock_subject):
            lock_subject(record_family, record_id)

    @staticmethod
    def linked_alert_case_lifecycle_lock_subject(
        record: ControlPlaneRecord,
    ) -> tuple[str, str] | None:
        if isinstance(record, AlertRecord):
            alert_id = record.alert_id
            case_id = record.case_id
        elif isinstance(record, CaseRecord):
            alert_id = record.alert_id
            case_id = record.case_id
        else:
            return None

        if not isinstance(alert_id, str) or not alert_id.strip():
            return None
        if not isinstance(case_id, str) or not case_id.strip():
            return None

        return (
            _LINKED_ALERT_CASE_LIFECYCLE_LOCK_FAMILY,
            f"alert:{alert_id}|case:{case_id}",
        )

    def build_lifecycle_transition_record(
        self,
        record: ControlPlaneRecord,
        *,
        existing_record: ControlPlaneRecord | None,
        transitioned_at: datetime | None = None,
        initial_transitioned_at_fallback: datetime | None = None,
        must_precede_transitioned_at: datetime | None = None,
        latest_transition: LifecycleTransitionRecord | None | object = (
            LATEST_LIFECYCLE_TRANSITION_UNSET
        ),
    ) -> LifecycleTransitionRecord | None:
        if isinstance(record, LifecycleTransitionRecord):
            return None
        if not hasattr(record, "lifecycle_state"):
            return None

        existing_lifecycle_state = (
            getattr(existing_record, "lifecycle_state", None)
            if existing_record is not None
            else None
        )
        next_lifecycle_state = getattr(record, "lifecycle_state", None)
        if not isinstance(next_lifecycle_state, str) or not next_lifecycle_state.strip():
            return None
        if latest_transition is LATEST_LIFECYCLE_TRANSITION_UNSET:
            latest_transition = self.latest_lifecycle_transition(
                record.record_family,
                record.record_id,
            )
        previous_lifecycle_state = existing_lifecycle_state
        if latest_transition is not None:
            if existing_record is None:
                raise ValueError(
                    f"{record.record_family} record {record.record_id!r} has orphaned "
                    "lifecycle transition history without a current-state record"
                )
            if existing_lifecycle_state != latest_transition.lifecycle_state:
                raise ValueError(
                    f"{record.record_family} record {record.record_id!r} lifecycle_state "
                    f"{existing_lifecycle_state!r} does not match latest lifecycle "
                    f"transition {latest_transition.transition_id!r} state "
                    f"{latest_transition.lifecycle_state!r}"
                )
            previous_lifecycle_state = latest_transition.lifecycle_state
        if previous_lifecycle_state == next_lifecycle_state:
            return None

        explicit_transitioned_at = transitioned_at is not None
        resolved_transitioned_at = (
            transitioned_at
            if transitioned_at is not None
            else (
                self.initial_lifecycle_transitioned_at(
                    record,
                    fallback=initial_transitioned_at_fallback,
                )
                if existing_record is None
                else datetime.now(timezone.utc)
            )
        )
        if (
            must_precede_transitioned_at is not None
            and resolved_transitioned_at >= must_precede_transitioned_at
        ):
            resolved_transitioned_at = must_precede_transitioned_at - timedelta(
                microseconds=1
            )
        if (
            latest_transition is not None
            and resolved_transitioned_at < latest_transition.transitioned_at
        ):
            if explicit_transitioned_at:
                raise ValueError(
                    "transitioned_at must not precede the latest lifecycle transition "
                    f"for {record.record_family} record {record.record_id!r}"
                )
            resolved_transitioned_at = latest_transition.transitioned_at + timedelta(
                microseconds=1
            )
        transition_timestamp = resolved_transitioned_at.astimezone(
            timezone.utc
        ).strftime("%Y%m%dT%H%M%S.%fZ")
        return LifecycleTransitionRecord(
            transition_id=self.lifecycle_transition_id(
                transition_timestamp=transition_timestamp,
                transitioned_at=resolved_transitioned_at,
                latest_transition=latest_transition,
            ),
            subject_record_family=record.record_family,
            subject_record_id=record.record_id,
            previous_lifecycle_state=(
                previous_lifecycle_state
                if isinstance(previous_lifecycle_state, str)
                and previous_lifecycle_state.strip()
                else None
            ),
            lifecycle_state=next_lifecycle_state,
            transitioned_at=resolved_transitioned_at,
            attribution=self.lifecycle_transition_attribution(record),
        )

    def lifecycle_transition_id(
        self,
        *,
        transition_timestamp: str,
        transitioned_at: datetime,
        latest_transition: LifecycleTransitionRecord | None,
    ) -> str:
        if (
            latest_transition is None
            or transitioned_at != latest_transition.transitioned_at
        ):
            return f"{transition_timestamp}:{uuid.uuid4()}"

        sequence = 1
        prefix = (
            f"{_SAME_TIMESTAMP_LIFECYCLE_TRANSITION_ID_PREFIX}{transition_timestamp}:"
        )
        if latest_transition.transition_id.startswith(prefix):
            sequence_text = latest_transition.transition_id[len(prefix) :].split(":", 1)[
                0
            ]
            if sequence_text.isdigit():
                sequence = int(sequence_text) + 1
        return f"{prefix}{sequence:06d}:{uuid.uuid4()}"

    def build_lifecycle_transition_records(
        self,
        record: ControlPlaneRecord,
        *,
        existing_record: ControlPlaneRecord | None,
        transitioned_at: datetime | None = None,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        if isinstance(record, LifecycleTransitionRecord):
            return ()
        if not hasattr(record, "lifecycle_state"):
            return ()

        latest_transition = self.latest_lifecycle_transition(
            record.record_family,
            record.record_id,
        )
        transition_records: list[LifecycleTransitionRecord] = []
        if latest_transition is None and existing_record is not None:
            anchor_transition = self.build_lifecycle_transition_record(
                existing_record,
                existing_record=None,
                must_precede_transitioned_at=transitioned_at,
                latest_transition=None,
            )
            if anchor_transition is not None:
                transition_records.append(anchor_transition)
                latest_transition = anchor_transition

        transition_record = self.build_lifecycle_transition_record(
            record,
            existing_record=existing_record,
            transitioned_at=transitioned_at,
            latest_transition=latest_transition,
        )
        if transition_record is not None:
            transition_records.append(transition_record)
        return tuple(transition_records)

    def initial_lifecycle_transitioned_at(
        self,
        record: ControlPlaneRecord,
        *,
        fallback: datetime | None = None,
    ) -> datetime:
        service = self._service
        if isinstance(record, AnalyticSignalRecord):
            if record.first_seen_at is not None:
                return record.first_seen_at
            if record.last_seen_at is not None:
                return record.last_seen_at
        elif isinstance(record, EvidenceRecord):
            return record.acquired_at
        elif isinstance(record, ObservationRecord):
            return record.observed_at
        elif isinstance(record, HuntRecord):
            return record.opened_at
        elif isinstance(record, HuntRunRecord):
            for candidate in (record.started_at, record.completed_at):
                if candidate is not None:
                    return candidate
        elif isinstance(record, (AlertRecord, CaseRecord)):
            reviewed_transitioned_at = service._reviewed_context_transitioned_at(record)
            if reviewed_transitioned_at is not None:
                return reviewed_transitioned_at
        elif isinstance(record, ApprovalDecisionRecord):
            if record.decided_at is not None:
                return record.decided_at
        elif isinstance(record, ActionRequestRecord):
            return record.requested_at
        elif isinstance(record, ActionExecutionRecord):
            return record.delegated_at
        elif isinstance(record, AITraceRecord):
            return record.generated_at
        elif isinstance(record, ReconciliationRecord):
            for candidate in (
                record.first_seen_at,
                record.last_seen_at,
                record.compared_at,
            ):
                if candidate is not None:
                    return candidate
        return fallback if fallback is not None else datetime.now(timezone.utc)

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        return self._service._store.latest_lifecycle_transition(record_family, record_id)

    def lifecycle_transition_attribution(
        self,
        record: ControlPlaneRecord,
    ) -> dict[str, object]:
        service = self._service
        actor_identities: tuple[str, ...] = ()
        source = "aegisops-control-plane"

        if isinstance(record, ObservationRecord):
            actor_identities = service._merge_linked_ids((), record.author_identity)
            source = "observation-author"
        elif isinstance(record, LeadRecord):
            actor_identities = service._merge_linked_ids((), record.triage_owner)
            source = "lead-triage-owner"
        elif isinstance(record, RecommendationRecord):
            actor_identities = service._merge_linked_ids((), record.review_owner)
            source = "recommendation-review-owner"
        elif isinstance(record, ActionRequestRecord):
            actor_identities = service._merge_linked_ids((), record.requester_identity)
            source = "action-request"
        elif isinstance(record, ApprovalDecisionRecord):
            actor_identities = service._merge_linked_ids(
                record.approver_identities,
                None,
            )
            source = "approval-decision"
        elif isinstance(record, HuntRecord):
            actor_identities = service._merge_linked_ids((), record.owner_identity)
            source = "hunt-owner"
        elif isinstance(record, AITraceRecord):
            actor_identities = service._merge_linked_ids((), record.reviewer_identity)
            source = "ai-trace-reviewer"

        return {
            "source": source,
            "actor_identities": actor_identities,
        }


class DetectionReconciliationResolver:
    def __init__(self, service: AegisOpsControlPlaneService) -> None:
        self._service = service

    def resolve_analytic_signal_id(
        self,
        *,
        analytic_signal_id: str | None,
        finding_id: str,
        correlation_key: str,
        substrate_detection_record_id: str | None,
        latest_reconciliation: ReconciliationRecord | None,
    ) -> str:
        service = self._service
        if analytic_signal_id is not None:
            return analytic_signal_id

        existing_signal_ids = service._merge_linked_ids(
            (
                latest_reconciliation.subject_linkage.get("analytic_signal_ids")
                if latest_reconciliation is not None
                else ()
            ),
            None,
        )
        if substrate_detection_record_id is not None:
            for existing_signal_id in existing_signal_ids:
                existing_signal = service._store.get(
                    AnalyticSignalRecord,
                    existing_signal_id,
                )
                if (
                    existing_signal is not None
                    and existing_signal.substrate_detection_record_id
                    == substrate_detection_record_id
                ):
                    return existing_signal_id

        if substrate_detection_record_id is None and len(existing_signal_ids) == 1:
            return existing_signal_ids[0]

        mint_material = "|".join(
            (
                finding_id,
                correlation_key,
                substrate_detection_record_id or "",
            )
        )
        return f"analytic-signal-{uuid.uuid5(uuid.NAMESPACE_URL, mint_material)}"

    def reconciliation_has_detection_lineage(self, record: ReconciliationRecord) -> bool:
        service = self._service
        return any(
            (
                record.analytic_signal_id is not None,
                bool(
                    service._merge_linked_ids(
                        record.subject_linkage.get("analytic_signal_ids"),
                        None,
                    )
                ),
                bool(
                    service._merge_linked_ids(
                        record.subject_linkage.get("substrate_detection_record_ids"),
                        None,
                    )
                ),
                bool(
                    service._merge_linked_ids(
                        record.subject_linkage.get("source_systems"),
                        None,
                    )
                ),
            )
        )

    def latest_detection_reconciliation_for_alert(
        self,
        alert_id: str,
    ) -> ReconciliationRecord | None:
        latest: ReconciliationRecord | None = None
        for record in self._service._store.list(ReconciliationRecord):
            if (
                record.alert_id != alert_id
                or not self.reconciliation_has_detection_lineage(record)
                or not self.reconciliation_is_wazuh_origin(record)
            ):
                continue
            if latest is None or (
                record.compared_at,
                record.reconciliation_id,
            ) > (
                latest.compared_at,
                latest.reconciliation_id,
            ):
                latest = record
        return latest

    def latest_detection_reconciliations_by_alert_id(
        self,
    ) -> dict[str, ReconciliationRecord]:
        latest_by_alert_id: dict[str, ReconciliationRecord] = {}
        for record in self._service._store.list(ReconciliationRecord):
            if (
                record.alert_id is None
                or not self.reconciliation_has_detection_lineage(record)
                or not self.reconciliation_is_wazuh_origin(record)
            ):
                continue
            current = latest_by_alert_id.get(record.alert_id)
            if current is None or (
                record.compared_at,
                record.reconciliation_id,
            ) > (
                current.compared_at,
                current.reconciliation_id,
            ):
                latest_by_alert_id[record.alert_id] = record
        return latest_by_alert_id

    def reconciliation_is_wazuh_origin(self, record: ReconciliationRecord) -> bool:
        service = self._service
        source_systems = service._merge_linked_ids(
            record.subject_linkage.get("source_systems"),
            None,
        )
        substrate_detection_record_ids = service._merge_linked_ids(
            record.subject_linkage.get("substrate_detection_record_ids"),
            None,
        )
        normalized_source_systems = tuple(
            source_system.strip().lower() for source_system in source_systems
        )
        normalized_substrate_detection_record_ids = tuple(
            detection_id.strip().lower()
            for detection_id in substrate_detection_record_ids
        )
        return "wazuh" in normalized_source_systems or any(
            detection_id.startswith("wazuh:")
            for detection_id in normalized_substrate_detection_record_ids
        )


class NativeDetectionAdmissionHelper:
    def __init__(
        self,
        service: AegisOpsControlPlaneService,
        *,
        normalize_admission_provenance: Callable[[object], dict[str, str] | None],
    ) -> None:
        self._service = service
        self._normalize_admission_provenance = normalize_admission_provenance

    def with_native_detection_admission_provenance(
        self,
        record: NativeDetectionRecord,
        *,
        admission_kind: str,
        admission_channel: str,
    ) -> NativeDetectionRecord:
        if (
            self._normalize_admission_provenance(
                record.metadata.get("admission_provenance")
            )
            is not None
        ):
            return record
        metadata = dict(record.metadata)
        metadata["admission_provenance"] = {
            "admission_kind": admission_kind,
            "admission_channel": admission_channel,
        }
        return replace(record, metadata=metadata)

    def normalize_substrate_detection_record_id(
        self,
        substrate_key: str,
        substrate_detection_record_id: str,
    ) -> str:
        namespaced_prefix = f"{substrate_key}:"
        if substrate_detection_record_id.startswith(namespaced_prefix):
            return substrate_detection_record_id
        return f"{namespaced_prefix}{substrate_detection_record_id}"


class LiveWazuhIntakeHandler:
    def __init__(
        self,
        service: AegisOpsControlPlaneService,
        intake: DetectionIntakeService,
    ) -> None:
        self._service = service
        self._intake = intake

    def ingest_wazuh_alert(
        self,
        *,
        raw_alert: Mapping[str, object],
        authorization_header: str | None,
        forwarded_proto: str | None,
        reverse_proxy_secret_header: str | None,
        peer_addr: str | None,
    ) -> FindingAlertIngestResult:
        service = self._service
        service._runtime_boundary_service.validate_wazuh_ingest_runtime()

        if not service._runtime_boundary_service.is_trusted_wazuh_ingest_peer(peer_addr):
            service._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="untrusted_peer",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest rejects requests that bypass the reviewed reverse proxy peer boundary"
            )

        if (forwarded_proto or "").strip().lower() != "https":
            service._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="forwarded_proto_not_https",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest requires the reviewed reverse proxy HTTPS boundary"
            )
        if not hmac.compare_digest(
            (reverse_proxy_secret_header or "").strip(),
            service._config.wazuh_ingest_reverse_proxy_secret,
        ):
            service._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="reverse_proxy_secret_mismatch",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest requires the reviewed reverse proxy boundary credential"
            )

        scheme, separator, supplied_secret = (authorization_header or "").partition(" ")
        if separator == "" or scheme != "Bearer" or supplied_secret.strip() == "":
            service._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="missing_bearer_secret",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest requires Authorization: Bearer <shared secret>"
            )
        if not hmac.compare_digest(
            supplied_secret.strip(),
            service._config.wazuh_ingest_shared_secret,
        ):
            service._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="bearer_secret_mismatch",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest bearer credential did not match the reviewed shared secret"
            )

        native_alert = service._require_mapping(raw_alert, "alert")
        source_family = service._normalize_optional_string(
            (
                service._require_mapping(
                    native_alert.get("data"),
                    "data",
                )
            ).get("source_family"),
            "data.source_family",
        )
        if source_family not in REVIEWED_LIVE_SOURCE_FAMILIES:
            service._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="unsupported_source_family",
                peer_addr=peer_addr,
                source_family=source_family,
            )
            raise ValueError(
                "live Wazuh ingest only admits the reviewed github_audit and entra_id live source families"
            )

        adapter = WazuhAlertAdapter()
        native_record = self._intake.with_native_detection_admission_provenance(
            adapter.build_native_detection_record(native_alert),
            admission_kind="live",
            admission_channel="live_wazuh_webhook",
        )
        ingest_result = self._intake.ingest_native_detection_record(
            adapter,
            native_record,
        )
        service._emit_structured_event(
            logging.INFO,
            "wazuh_ingest_admitted",
            peer_addr=peer_addr,
            source_family=source_family,
            disposition=ingest_result.disposition,
            alert_id=ingest_result.alert.alert_id,
            finding_id=ingest_result.alert.finding_id,
            reconciliation_id=ingest_result.reconciliation.reconciliation_id,
        )
        return ingest_result
