from __future__ import annotations

from typing import Iterable, Mapping, Protocol, Type

from ..models import (
    AlertRecord,
    CaseRecord,
    ControlPlaneRecord,
    DetectorLifecycleRecord,
    EvidenceRecord,
    FalsePositiveReviewRecord,
    ReconciliationRecord,
    SourceHealthRecord,
    SuppressionProposalRecord,
)
from ..runtime.service_snapshots import RecordInspectionSnapshot, _json_ready


RECORD_SEARCH_RECORD_TYPES: tuple[Type[ControlPlaneRecord], ...] = (
    AlertRecord,
    CaseRecord,
    EvidenceRecord,
    DetectorLifecycleRecord,
    FalsePositiveReviewRecord,
    SuppressionProposalRecord,
    SourceHealthRecord,
)
RECORD_SEARCH_RECORD_TYPES_BY_FAMILY: dict[str, Type[ControlPlaneRecord]] = {
    record_type.record_family: record_type for record_type in RECORD_SEARCH_RECORD_TYPES
}
RECORD_SEARCH_BLOCKED_TERMS = (
    "raw:",
    "raw wazuh",
    "raw source",
    "source-native",
    "source native",
    "close case",
    "reconcile",
    "approve detector",
    "suppress signal",
)
RECORD_SEARCH_COMMON_REVIEWED_FIELDS = (
    "record_family",
    "record_id",
    "source_family",
    "lifecycle_state",
)
RECORD_SEARCH_REVIEWED_FIELDS_BY_FAMILY = {
    "alert": (
        "alert_id",
        "analytic_signal_id",
        "case_id",
        "finding_id",
        "reviewed_context",
    ),
    "case": (
        "case_id",
        "alert_id",
        "finding_id",
        "evidence_ids",
        "reviewed_context",
    ),
    "evidence": (
        "evidence_id",
        "alert_id",
        "case_id",
    ),
    "detector_lifecycle": (
        "detector_lifecycle_id",
        "owner",
        "source_catalog_entry",
        "detector_identifier",
        "expected_signal_posture",
        "review_cadence",
        "rollback_owner",
        "disable_owner",
        "lifecycle_audit_references",
        "disabled_reason",
        "rollback_reason",
        "review_overdue_reason",
    ),
    "false_positive_review": (
        "false_positive_review_id",
        "detector_lifecycle_id",
        "source_catalog_entry",
        "alert_id",
        "case_id",
        "evidence_ids",
        "owner",
        "disposition",
        "disposition_rationale",
        "dispute_state",
        "recurrence_posture",
        "review_evidence_references",
        "source_signal_handling",
    ),
    "suppression_proposal": (
        "suppression_proposal_id",
        "detector_lifecycle_id",
        "source_catalog_entry",
        "alert_id",
        "case_id",
        "evidence_ids",
        "owner",
        "rationale",
        "citation_references",
        "expires_at",
        "review_cadence",
        "expected_signal_impact",
        "scope",
        "source_signal_handling",
    ),
    "source_health": (
        "source_health_id",
        "source_catalog_entry",
        "health_state",
        "reviewed_state",
        "reviewed_at",
        "observed_at",
        "detector_drift",
        "credential_posture",
        "evidence_references",
        "operator_visible_reason",
    ),
}


class RecordSearchStore(Protocol):
    def get(self, record_type: Type[ControlPlaneRecord], record_id: str) -> object | None:
        ...

    def list(self, record_type: Type[ControlPlaneRecord]) -> tuple[object, ...]:
        ...


class RecordSearchServiceDependencies(Protocol):
    _store: RecordSearchStore

    def _normalize_optional_string(
        self,
        value: object,
        field_name: str,
    ) -> str | None:
        ...

    def _reviewed_operator_source_family(
        self,
        reviewed_context: object,
    ) -> str | None:
        ...

    def _case_is_in_reviewed_operator_slice(self, case: CaseRecord) -> bool:
        ...

    def _alert_is_in_reviewed_operator_slice(self, alert: AlertRecord) -> bool:
        ...

    def _latest_detection_reconciliation_for_alert(
        self,
        alert_id: str,
    ) -> ReconciliationRecord | None:
        ...

    def _reconciliation_is_wazuh_origin(
        self,
        reconciliation: ReconciliationRecord,
    ) -> bool:
        ...

    def _linked_id_exists(self, values: object, expected_id: str) -> bool:
        ...


class RecordSearchInspectionService:
    def __init__(
        self,
        service: RecordSearchServiceDependencies,
        *,
        record_to_dict,
    ) -> None:
        self._service = service
        self._record_to_dict = record_to_dict

    def inspect_record_search(
        self,
        *,
        query: str,
        record_families: Iterable[str] | None = None,
        source_family: str | None = None,
        lifecycle_state: str | None = None,
    ) -> RecordInspectionSnapshot:
        search_query = self._normalize_record_search_query(query)
        selected_families = self._normalize_record_search_families(record_families)
        normalized_source_family = self._normalize_record_search_filter(
            source_family,
            "source_family",
        )
        normalized_lifecycle_state = self._normalize_record_search_filter(
            lifecycle_state,
            "lifecycle_state",
        )

        records: list[dict[str, object]] = []
        for family in selected_families:
            record_type = RECORD_SEARCH_RECORD_TYPES_BY_FAMILY[family]
            for record in self._service._store.list(record_type):
                if not isinstance(record, ControlPlaneRecord):
                    continue
                result = self._record_search_result(
                    record,
                    query=search_query,
                    source_family=normalized_source_family,
                    lifecycle_state=normalized_lifecycle_state,
                )
                if result is not None:
                    records.append(result)

        records = sorted(
            records,
            key=lambda result: (
                str(result["record_family"]),
                str(result["record_id"]),
            ),
        )
        return RecordInspectionSnapshot(
            read_only=True,
            record_family="record_search",
            total_records=len(records),
            records=tuple(records),
        )

    @staticmethod
    def _normalize_record_search_query(query: str) -> str:
        if not isinstance(query, str):
            raise ValueError("unsupported record search query")
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("unsupported record search query")

        lowered_query = normalized_query.lower()
        if any(term in lowered_query for term in RECORD_SEARCH_BLOCKED_TERMS):
            raise ValueError("unsupported record search query")
        return normalized_query

    @staticmethod
    def _normalize_record_search_families(
        record_families: Iterable[str] | None,
    ) -> tuple[str, ...]:
        if record_families is None:
            return tuple(RECORD_SEARCH_RECORD_TYPES_BY_FAMILY)

        families: list[str] = []
        for family in record_families:
            normalized_family = str(family).strip()
            if normalized_family not in RECORD_SEARCH_RECORD_TYPES_BY_FAMILY:
                known_families = ", ".join(sorted(RECORD_SEARCH_RECORD_TYPES_BY_FAMILY))
                raise ValueError(
                    f"Unsupported search record family {normalized_family!r}; "
                    f"expected one of: {known_families}"
                )
            if normalized_family not in families:
                families.append(normalized_family)
        if not families:
            raise ValueError("unsupported record search query")
        return tuple(families)

    def _record_search_result(
        self,
        record: ControlPlaneRecord,
        *,
        query: str,
        source_family: str | None,
        lifecycle_state: str | None,
    ) -> dict[str, object] | None:
        payload = self._record_to_dict(record)
        family = record.record_family
        record_source_family = self._record_search_source_family(record)

        if record_source_family is None:
            return None
        if source_family is not None and record_source_family != source_family:
            return None

        record_lifecycle_state = payload.get("lifecycle_state")
        if not self._record_search_lifecycle_state_matches(
            record_lifecycle_state,
            lifecycle_state,
        ):
            return None

        if isinstance(record, SourceHealthRecord):
            if record.cache_sourced:
                raise ValueError("stale-cache record search result refused")
            if record.source_native_authority or record.display_state_authority:
                raise ValueError("raw-source authority record search result refused")

        search_payload = {
            **payload,
            "record_family": family,
            "record_id": record.record_id,
            "source_family": record_source_family,
        }
        if not self._record_search_payload_matches(search_payload, query):
            return None

        record_id = record.record_id
        route = self._record_search_route(record)
        if route is None:
            return None
        return {
            "record_family": family,
            "record_id": record_id,
            "id": f"{family}:{record_id}",
            "source_family": record_source_family,
            "lifecycle_state": record_lifecycle_state,
            "matched_query": query,
            "route": route,
            "route_kind": "reviewed_surface",
            "authority": "navigation_only",
            "raw_source_authority": False,
            "summary": self._record_search_summary(payload, family, record_id),
        }

    def _record_search_source_family(self, record: ControlPlaneRecord) -> str | None:
        if isinstance(record, AlertRecord):
            if not self._service._alert_is_in_reviewed_operator_slice(record):
                return None
            return self._record_search_alert_source_family(record)

        if isinstance(record, CaseRecord):
            if not self._service._case_is_in_reviewed_operator_slice(record):
                return None
            return self._record_search_case_source_family(record)

        if isinstance(record, EvidenceRecord):
            if record.case_id is not None:
                case = self._service._store.get(CaseRecord, record.case_id)
                if (
                    isinstance(case, CaseRecord)
                    and self._service._case_is_in_reviewed_operator_slice(case)
                ):
                    source_family = self._record_search_case_source_family(case)
                    if source_family is not None:
                        return source_family
            if record.alert_id is not None:
                alert = self._service._store.get(AlertRecord, record.alert_id)
                if (
                    isinstance(alert, AlertRecord)
                    and self._service._alert_is_in_reviewed_operator_slice(alert)
                ):
                    return self._record_search_alert_source_family(alert)
            return None

        if isinstance(
            record,
            (
                DetectorLifecycleRecord,
                FalsePositiveReviewRecord,
                SuppressionProposalRecord,
                SourceHealthRecord,
            ),
        ):
            return record.source_family.strip()

        return None

    def _record_search_case_source_family(self, case: CaseRecord) -> str | None:
        source_family = self._service._reviewed_operator_source_family(
            case.reviewed_context
        )
        if source_family is not None:
            return source_family

        if case.alert_id is not None:
            alert = self._service._store.get(AlertRecord, case.alert_id)
            if isinstance(alert, AlertRecord):
                source_family = self._service._reviewed_operator_source_family(
                    alert.reviewed_context
                )
                if source_family is not None:
                    return source_family
            reconciliation = self._record_search_reviewed_reconciliation_for_alert(
                case.alert_id,
                case_id=case.case_id,
            )
            if reconciliation is not None:
                return self._reviewed_reconciliation_source_family(reconciliation)

        return None

    def _record_search_alert_source_family(self, alert: AlertRecord) -> str | None:
        source_family = self._service._reviewed_operator_source_family(
            alert.reviewed_context
        )
        if source_family is not None:
            return source_family

        reconciliation = self._record_search_reviewed_reconciliation_for_alert(
            alert.alert_id
        )
        if reconciliation is None:
            return None
        return self._reviewed_reconciliation_source_family(reconciliation)

    def _record_search_reviewed_reconciliation_for_alert(
        self,
        alert_id: str,
        *,
        case_id: str | None = None,
    ) -> ReconciliationRecord | None:
        reconciliation = self._service._latest_detection_reconciliation_for_alert(
            alert_id
        )
        if reconciliation is None or not self._service._reconciliation_is_wazuh_origin(
            reconciliation
        ):
            return None
        if not self._service._linked_id_exists(
            reconciliation.subject_linkage.get("alert_ids"),
            alert_id,
        ):
            return None
        if case_id is not None and not self._service._linked_id_exists(
            reconciliation.subject_linkage.get("case_ids"),
            case_id,
        ):
            return None
        return reconciliation

    def _reviewed_reconciliation_source_family(
        self,
        reconciliation: ReconciliationRecord,
    ) -> str | None:
        return self._service._reviewed_operator_source_family(
            reconciliation.subject_linkage.get("reviewed_source_profile")
        )

    @staticmethod
    def _record_search_payload_matches(
        payload: Mapping[str, object],
        query: str,
    ) -> bool:
        haystack = " ".join(
            value.lower()
            for value in RecordSearchInspectionService._record_search_payload_values(
                payload
            )
        )
        return query.lower() in haystack

    @staticmethod
    def _record_search_payload_values(
        payload: Mapping[str, object],
    ) -> tuple[str, ...]:
        family = payload.get("record_family")
        selected_fields = (
            *RECORD_SEARCH_COMMON_REVIEWED_FIELDS,
            *RECORD_SEARCH_REVIEWED_FIELDS_BY_FAMILY.get(str(family), ()),
        )
        values: list[str] = []
        for field_name in selected_fields:
            if field_name in payload:
                values.extend(
                    RecordSearchInspectionService._record_search_value_text(
                        _json_ready(payload[field_name])
                    )
                )
        return tuple(values)

    @staticmethod
    def _record_search_value_text(value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, Mapping):
            text: list[str] = []
            for nested_value in value.values():
                text.extend(
                    RecordSearchInspectionService._record_search_value_text(
                        nested_value
                    )
                )
            return tuple(text)
        if isinstance(value, (list, tuple)):
            text: list[str] = []
            for item in value:
                text.extend(
                    RecordSearchInspectionService._record_search_value_text(item)
                )
            return tuple(text)
        rendered = str(value).strip()
        if not rendered:
            return ()
        return (rendered,)

    def _record_search_route(self, record: ControlPlaneRecord) -> str | None:
        if isinstance(record, AlertRecord):
            return f"/operator/alerts/{record.record_id}"
        if isinstance(record, CaseRecord):
            return f"/operator/cases/{record.record_id}"
        if isinstance(record, EvidenceRecord):
            return self._reviewed_anchor_route(
                case_id=record.case_id,
                alert_id=record.alert_id,
            )
        if isinstance(record, DetectorLifecycleRecord):
            return "/operator/detectors"
        if isinstance(record, (FalsePositiveReviewRecord, SuppressionProposalRecord)):
            return (
                self._reviewed_anchor_route(
                    case_id=record.case_id,
                    alert_id=record.alert_id,
                )
                or "/operator/detectors"
            )
        if isinstance(record, SourceHealthRecord):
            return "/operator/source-health"
        return None

    def _reviewed_anchor_route(
        self,
        *,
        case_id: str | None,
        alert_id: str | None,
    ) -> str | None:
        if case_id is not None:
            case = self._service._store.get(CaseRecord, case_id)
            if (
                isinstance(case, CaseRecord)
                and self._service._case_is_in_reviewed_operator_slice(case)
            ):
                return f"/operator/cases/{case.case_id}"
        if alert_id is not None:
            alert = self._service._store.get(AlertRecord, alert_id)
            if (
                isinstance(alert, AlertRecord)
                and self._service._alert_is_in_reviewed_operator_slice(alert)
            ):
                return f"/operator/alerts/{alert.alert_id}"
        return None

    def _normalize_record_search_filter(
        self,
        value: str | None,
        field_name: str,
    ) -> str | None:
        normalized = self._service._normalize_optional_string(value, field_name)
        if normalized is None:
            return None
        return normalized.strip()

    @staticmethod
    def _record_search_lifecycle_state_matches(
        record_lifecycle_state: object,
        lifecycle_state: str | None,
    ) -> bool:
        if lifecycle_state is None:
            return True
        return str(record_lifecycle_state).strip() == lifecycle_state

    @staticmethod
    def _record_search_summary(
        payload: Mapping[str, object],
        record_family: str,
        record_id: str,
    ) -> str:
        for field_name in (
            "operator_visible_reason",
            "disposition_rationale",
            "rationale",
            "expected_signal_posture",
            "lifecycle_state",
        ):
            value = payload.get(field_name)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return f"Reviewed {record_family} record {record_id}"
